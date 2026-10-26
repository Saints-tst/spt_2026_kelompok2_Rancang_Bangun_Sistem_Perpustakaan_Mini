const express = require('express');
const sqlite3 = require('sqlite3').verbose();
const app = express();
const PORT = 3001; // Port khusus untuk Server 1

// Middleware untuk memproses data format JSON
app.use(express.json());

// Sambungan ke Pangkalan Data SQLite (Penyimpanan Terpusat)
const db = new sqlite3.Database('./perpustakaan.db', (err) => {
    if (err) {
        console.error('Ralat menyambung ke pangkalan data:', err.message);
    } else {
        console.log('Berjaya disambungkan ke pangkalan data SQLite (Server 1).');
        
        // Membina jadual 'buku' berdasarkan spesifikasi Bab IV Proposal
        db.run(`CREATE TABLE IF NOT EXISTS buku (
            id_buku INTEGER PRIMARY KEY AUTOINCREMENT,
            kode_buku TEXT UNIQUE,
            judul TEXT,
            penulis TEXT,
            penerbit TEXT,
            tahun INTEGER,
            stok INTEGER
        )`);
    }
});

// ================= Endpoints API Server 1 =================

// 1. Dapatkan semua senarai buku atau cari buku
app.get('/api/buku', (req, res) => {
    const { search } = req.query;
    let query = `SELECT * FROM buku`;
    let params = [];

    if (search) {
        query += ` WHERE judul LIKE ? OR penulis LIKE ? OR kode_buku LIKE ?`;
        params = [`%${search}%`, `%${search}%`, `%${search}%`];
    }

    db.all(query, params, (err, rows) => {
        if (err) {
            return res.status(500).json({ kejayaan: false, ralat: err.message });
        }
        res.json({ kejayaan: true, data: rows });
    });
});

// 2. Dapatkan maklumat terperinci buku mengikut ID
app.get('/api/buku/:id', (req, res) => {
    const { id } = req.params;
    db.get(`SELECT * FROM buku WHERE id_buku = ?`, [id], (err, row) => {
        if (err) {
            return res.status(500).json({ kejayaan: false, ralat: err.message });
        }
        if (!row) {
            return res.status(404).json({ kejayaan: false, ralat: 'Buku tidak ditemui' });
        }
        res.json({ kejayaan: true, data: row });
    });
});

// 3. Menambah data buku baharu
app.post('/api/buku', (req, res) => {
    const { kode_buku, judul, penulis, penerbit, tahun, stok } = req.body;
    
    if (!kode_buku || !judul || !penulis || !stok) {
        return res.status(400).json({ kejayaan: false, ralat: 'Sila lengkapkan maklumat wajib (kode_buku, judul, penulis, stok).' });
    }

    const query = `INSERT INTO buku (kode_buku, judul, penulis, penerbit, tahun, stok) VALUES (?, ?, ?, ?, ?, ?)`;
    
    db.run(query, [kode_buku, judul, penulis, penerbit, tahun, stok], function(err) {
        if (err) {
            return res.status(400).json({ kejayaan: false, ralat: 'Ralat: Kod buku mungkin sudah wujud.' });
        }
        res.status(201).json({
            kejayaan: true,
            mesej: 'Data buku berjaya ditambah',
            id_buku: this.lastID
        });
    });
});

// 4. Mengemas kini maklumat buku
app.put('/api/buku/:id', (req, res) => {
    const { id } = req.params;
    const { kode_buku, judul, penulis, penerbit, tahun, stok } = req.body;
    
    const query = `UPDATE buku SET kode_buku = ?, judul = ?, penulis = ?, penerbit = ?, tahun = ?, stok = ? WHERE id_buku = ?`;

    db.run(query, [kode_buku, judul, penulis, penerbit, tahun, stok, id], function(err) {
        if (err) {
            return res.status(400).json({ kejayaan: false, ralat: err.message });
        }
        if (this.changes === 0) {
            return res.status(404).json({ kejayaan: false, ralat: 'Buku tidak ditemui' });
        }
        res.json({ kejayaan: true, mesej: 'Maklumat buku berjaya dikemas kini' });
    });
});

// 5. Menghapus data buku
app.delete('/api/buku/:id', (req, res) => {
    const { id } = req.params;
    db.run(`DELETE FROM buku WHERE id_buku = ?`, [id], function(err) {
        if (err) {
            return res.status(500).json({ kejayaan: false, ralat: err.message });
        }
        if (this.changes === 0) {
            return res.status(404).json({ kejayaan: false, ralat: 'Buku tidak ditemui' });
        }
        res.json({ kejayaan: true, mesej: 'Data buku berjaya dipadam' });
    });
});

// 6. Mengemas kini stok buku (untuk interaksi dengan Server 2)
app.patch('/api/buku/:id/stok', (req, res) => {
    const { id } = req.params;
    const { stok } = req.body;

    db.run(`UPDATE buku SET stok = ? WHERE id_buku = ?`, [stok, id], function(err) {
        if (err) {
            return res.status(400).json({ kejayaan: false, ralat: err.message });
        }
        if (this.changes === 0) {
            return res.status(404).json({ kejayaan: false, ralat: 'Buku tidak ditemui' });
        }
        res.json({ kejayaan: true, mesej: 'Stok buku berjaya dikemas kini' });
    });
});

// Menjalankan Server 1
app.listen(PORT, () => {
    console.log(`Server 1 (Pengolahan Data Buku) sedang aktif di http://localhost:${PORT}`);
});