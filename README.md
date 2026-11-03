# 📚 Sistem Perpustakaan Mini

Prototipe sistem perpustakaan berbasis jaringan dengan arsitektur **client-server**: dua server, satu client, dan satu database terpusat. Dibuat untuk mata kuliah **Sistem Paralel dan Terdistribusi (SPT)**.

## Arsitektur

```
              ┌──────────┐
              │  CLIENT  │
              └────┬─────┘
          ┌────────┴────────┐
          ▼                 ▼
    ┌──────────┐      ┌──────────┐
    │ SERVER 1 │      │ SERVER 2 │
    │   Buku   │      │ Pinjam & │
    │          │      │  Denda   │
    └────┬─────┘      └────┬─────┘
         └────────┬────────┘
                  ▼
            ┌──────────┐
            │ DATABASE │
            └──────────┘
```

| Komponen | Peran |
|----------|-------|
| **Client** | Antarmuka pengguna (login, cari buku, pinjam, kembalikan) |
| **Server 1** | Pengelolaan data buku (tambah, ubah, hapus, cari, status ketersediaan) |
| **Server 2** | Transaksi peminjaman, pengembalian, dan perhitungan denda |
| **Database** | Penyimpanan terpusat data buku, anggota, dan transaksi |

## Fitur Utama

- CRUD dan pencarian buku (judul, penulis, kategori, kode)
- Pencatatan peminjaman dan pengembalian
- Perhitungan denda otomatis (contoh: Rp1.000/hari/buku)
- Riwayat peminjaman anggota
- Keamanan dasar: autentikasi petugas, pembatasan hak akses, validasi input

## Basis Data

Tabel utama: `buku`, `anggota`, `peminjaman`, `pengembalian`, `denda`

## Teknologi

Stack disesuaikan dengan kemampuan tim.

- **DBMS:** MySQL / MariaDB / PostgreSQL
- **Server & Client:** Python 3 dan Browser

## Rencana Pengujian

Koneksi client–server, CRUD buku, peminjaman, pengembalian tepat waktu, pengembalian terlambat (denda), dan konsistensi database.

## Pengembangan Lanjutan

- Antarmuka client yang responsif
- REST API untuk komunikasi client–server
- Laporan peminjaman dan denda
- Dashboard statistik
- Backup dan restore database

## Tim — Kelompok 2

| Nama | NIM | Tugas |
|------|-----|-------|
| Darmawansya | 23210080 | Server 1 (data buku) dan Server 2 (pinjam, kembali, denda) |
| Muhammad Fayyadh Alghifari | 23210010 | Client (antarmuka) |
| Maulidzhan Syam Ikraam | 23210095 | Database & konfigurasi jaringan |
| Rahmad Fadli | 23210129 | Pengujian, keamanan, dokumentasi |

---

**Dosen Pengampu:** Ahmad Mujahid Abdurrahman, S.Kom, M.T
**Program Studi Ilmu Komputer** · Universitas Bina Bangsa Getsempena, Banda Aceh

> ⚠️ Proyek ini adalah prototipe untuk keperluan perkuliahan, bukan untuk operasional perpustakaan yang sebenarnya.
