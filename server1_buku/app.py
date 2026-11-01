from flask import Flask, request, jsonify
from flask_cors import CORS
import mysql.connector
from mysql.connector import IntegrityError
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
}

def db():
    return mysql.connector.connect(**DB_CONFIG)


# 1. Cari / tampilkan semua buku
@app.get("/buku")
def cari_buku():
    q = f"%{request.args.get('q', '')}%"
    con = db(); cur = con.cursor(dictionary=True)
    cur.execute("""SELECT * FROM buku
                   WHERE judul LIKE %s OR penulis LIKE %s OR kode_buku LIKE %s
                   ORDER BY id_buku""", (q, q, q))
    data = cur.fetchall()
    con.close()
    return jsonify(data)


# 2. Detail satu buku + status ketersediaan
@app.get("/buku/<int:id_buku>")
def detail_buku(id_buku):
    con = db(); cur = con.cursor(dictionary=True)
    cur.execute("SELECT * FROM buku WHERE id_buku = %s", (id_buku,))
    buku = cur.fetchone()
    con.close()
    if not buku:
        return jsonify(error="Buku tidak ditemukan"), 404
    buku["status"] = "tersedia" if buku["stok"] > 0 else "habis"
    return jsonify(buku)


# 3. Tambah buku
@app.post("/buku")
def tambah_buku():
    d = request.get_json(silent=True) or {}
    if not d.get("kode_buku") or not d.get("judul"):
        return jsonify(error="kode_buku dan judul wajib diisi"), 400
    if int(d.get("stok", 0)) < 0:
        return jsonify(error="stok tidak boleh negatif"), 400
    con = db(); cur = con.cursor()
    try:
        cur.execute("""INSERT INTO buku (kode_buku, judul, penulis, penerbit, tahun, stok)
                       VALUES (%s, %s, %s, %s, %s, %s)""",
                    (d["kode_buku"], d["judul"], d.get("penulis"),
                     d.get("penerbit"), d.get("tahun"), d.get("stok", 0)))
        con.commit()
        new_id = cur.lastrowid
    except IntegrityError:
        con.close()
        return jsonify(error="kode_buku sudah dipakai"), 409
    con.close()
    return jsonify(pesan="Buku ditambahkan", id_buku=new_id), 201


# 4. Ubah buku
@app.put("/buku/<int:id_buku>")
def ubah_buku(id_buku):
    d = request.get_json(silent=True) or {}
    if not d.get("kode_buku") or not d.get("judul"):
        return jsonify(error="kode_buku dan judul wajib diisi"), 400
    con = db(); cur = con.cursor()
    try:
        cur.execute("""UPDATE buku SET kode_buku=%s, judul=%s, penulis=%s,
                       penerbit=%s, tahun=%s, stok=%s WHERE id_buku=%s""",
                    (d["kode_buku"], d["judul"], d.get("penulis"),
                     d.get("penerbit"), d.get("tahun"), d.get("stok", 0), id_buku))
        con.commit()
        ada = cur.rowcount > 0
    except IntegrityError:
        con.close()
        return jsonify(error="kode_buku sudah dipakai buku lain"), 409
    con.close()
    if not ada:
        return jsonify(error="Buku tidak ditemukan atau tidak ada perubahan"), 404
    return jsonify(pesan="Buku diperbarui")


# 5. Hapus buku
@app.delete("/buku/<int:id_buku>")
def hapus_buku(id_buku):
    con = db(); cur = con.cursor()
    try:
        cur.execute("DELETE FROM buku WHERE id_buku = %s", (id_buku,))
        con.commit()
        ada = cur.rowcount > 0
    except IntegrityError:
        con.close()
        return jsonify(error="Buku masih punya riwayat peminjaman, tidak bisa dihapus"), 409
    con.close()
    if not ada:
        return jsonify(error="Buku tidak ditemukan"), 404
    return jsonify(pesan="Buku dihapus")


# 6. Ubah stok (dipanggil Server 2): delta -1 saat pinjam, +1 saat kembali
@app.put("/buku/<int:id_buku>/stok")
def ubah_stok(id_buku):
    d = request.get_json(silent=True) or {}
    if "delta" not in d:
        return jsonify(error="delta wajib diisi"), 400
    delta = int(d["delta"])
    con = db(); cur = con.cursor()
    cur.execute("""UPDATE buku SET stok = stok + %s
                   WHERE id_buku = %s AND stok + %s >= 0""",
                (delta, id_buku, delta))
    con.commit()
    ok = cur.rowcount > 0
    con.close()
    if not ok:
        return jsonify(error="Stok tidak cukup atau buku tidak ditemukan"), 409
    return jsonify(pesan="Stok diperbarui")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)