import os
from datetime import date, timedelta

import mysql.connector
import requests
from dotenv import load_dotenv
from flask import Flask, jsonify, request
from flask_cors import CORS

load_dotenv()

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}
SERVER1_URL = os.getenv("SERVER1_URL", "http://localhost:5001")
TARIF_DENDA = int(os.getenv("TARIF_DENDA", 1000))   # Rp per hari per buku
LAMA_PINJAM = int(os.getenv("LAMA_PINJAM", 7))      # hari


def db():
    return mysql.connector.connect(**DB_CONFIG)


def rapikan(rows):
    """Ubah objek tanggal menjadi teks agar aman dikirim sebagai JSON."""
    for r in rows:
        for k, v in r.items():
            if isinstance(v, date):
                r[k] = v.isoformat()
    return rows


def ubah_stok_server1(id_buku, delta):
    """Minta Server 1 mengubah stok. Mengembalikan response, atau None jika Server 1 mati."""
    try:
        return requests.put(f"{SERVER1_URL}/buku/{id_buku}/stok",
                            json={"delta": delta}, timeout=5)
    except requests.RequestException:
        return None


# 1. Catat peminjaman
@app.post("/pinjam")
def pinjam():
    d = request.get_json(silent=True) or {}
    try:
        id_anggota = int(d.get("id_anggota"))
        id_buku = int(d.get("id_buku"))
    except (TypeError, ValueError):
        return jsonify(error="id_anggota dan id_buku wajib diisi (angka)"), 400

    con = db()
    cur = con.cursor(dictionary=True)

    # a. cek anggota
    cur.execute("SELECT nama FROM anggota WHERE id_anggota = %s", (id_anggota,))
    anggota = cur.fetchone()
    if not anggota:
        con.close()
        return jsonify(error="Anggota tidak ditemukan"), 404

    # b. kurangi stok lewat Server 1 (sekaligus cek ketersediaan)
    r = ubah_stok_server1(id_buku, -1)
    if r is None:
        con.close()
        return jsonify(error="Server 1 tidak dapat dihubungi"), 503
    if r.status_code != 200:
        con.close()
        return jsonify(error="Buku tidak tersedia atau tidak ditemukan"), 409

    # c. catat transaksi
    tgl_pinjam = date.today()
    jatuh_tempo = tgl_pinjam + timedelta(days=LAMA_PINJAM)
    try:
        cur.execute("""INSERT INTO peminjaman
                       (id_anggota, id_buku, tgl_pinjam, tgl_jatuh_tempo, status)
                       VALUES (%s, %s, %s, %s, 'dipinjam')""",
                    (id_anggota, id_buku, tgl_pinjam, jatuh_tempo))
        con.commit()
        id_peminjaman = cur.lastrowid
    except Exception:
        con.rollback()
        con.close()
        ubah_stok_server1(id_buku, +1)   # batalkan pengurangan stok
        return jsonify(error="Gagal mencatat peminjaman"), 500

    con.close()
    return jsonify(pesan="Peminjaman dicatat",
                   id_peminjaman=id_peminjaman,
                   anggota=anggota["nama"],
                   tgl_pinjam=tgl_pinjam.isoformat(),
                   tgl_jatuh_tempo=jatuh_tempo.isoformat()), 201


# 2. Catat pengembalian + hitung denda
@app.post("/kembali")
def kembali():
    d = request.get_json(silent=True) or {}
    try:
        id_peminjaman = int(d.get("id_peminjaman"))
    except (TypeError, ValueError):
        return jsonify(error="id_peminjaman wajib diisi (angka)"), 400

    con = db()
    cur = con.cursor(dictionary=True)
    cur.execute("SELECT * FROM peminjaman WHERE id_peminjaman = %s", (id_peminjaman,))
    p = cur.fetchone()
    if not p:
        con.close()
        return jsonify(error="Transaksi tidak ditemukan"), 404
    if p["status"] != "dipinjam":
        con.close()
        return jsonify(error="Buku sudah dikembalikan"), 409

    hari_ini = date.today()
    telat = max(0, (hari_ini - p["tgl_jatuh_tempo"]).days)
    denda = telat * TARIF_DENDA

    try:
        cur.execute("""INSERT INTO pengembalian (id_peminjaman, tgl_kembali, keterlambatan)
                       VALUES (%s, %s, %s)""", (id_peminjaman, hari_ini, telat))
        id_denda = None
        if denda > 0:
            cur.execute("""INSERT INTO denda (id_peminjaman, jumlah, status_bayar)
                           VALUES (%s, %s, 'belum')""", (id_peminjaman, denda))
            id_denda = cur.lastrowid
        cur.execute("UPDATE peminjaman SET status = 'dikembalikan' WHERE id_peminjaman = %s",
                    (id_peminjaman,))
        con.commit()
    except Exception:
        con.rollback()
        con.close()
        return jsonify(error="Gagal mencatat pengembalian"), 500
    con.close()

    # kembalikan stok lewat Server 1
    r = ubah_stok_server1(p["id_buku"], +1)
    hasil = {
        "pesan": "Pengembalian dicatat",
        "tgl_kembali": hari_ini.isoformat(),
        "keterlambatan_hari": telat,
        "denda": denda,
        "id_denda": id_denda,
    }
    if r is None or r.status_code != 200:
        hasil["peringatan"] = "Transaksi tersimpan, tetapi stok belum diperbarui di Server 1"
    return jsonify(hasil)


# 3. Riwayat peminjaman satu anggota
@app.get("/riwayat/<int:id_anggota>")
def riwayat(id_anggota):
    con = db()
    cur = con.cursor(dictionary=True)
    cur.execute("""
        SELECT p.id_peminjaman, b.kode_buku, b.judul,
               p.tgl_pinjam, p.tgl_jatuh_tempo, p.status,
               k.tgl_kembali, k.keterlambatan,
               n.id_denda, n.jumlah AS denda, n.status_bayar
        FROM peminjaman p
        JOIN buku b ON b.id_buku = p.id_buku
        LEFT JOIN pengembalian k ON k.id_peminjaman = p.id_peminjaman
        LEFT JOIN denda n ON n.id_peminjaman = p.id_peminjaman
        WHERE p.id_anggota = %s
        ORDER BY p.id_peminjaman DESC""", (id_anggota,))
    data = rapikan(cur.fetchall())
    con.close()
    return jsonify(data)


# 4. Tandai denda lunas
@app.put("/denda/<int:id_denda>/bayar")
def bayar_denda(id_denda):
    con = db()
    cur = con.cursor()
    cur.execute("""UPDATE denda SET status_bayar = 'lunas'
                   WHERE id_denda = %s AND status_bayar = 'belum'""", (id_denda,))
    con.commit()
    ok = cur.rowcount > 0
    con.close()
    if not ok:
        return jsonify(error="Denda tidak ditemukan atau sudah lunas"), 404
    return jsonify(pesan="Denda dilunasi")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=True)