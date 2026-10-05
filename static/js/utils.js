/*
 * Helper JavaScript yang dipakai bersama oleh beberapa halaman
 * (Projects dan Education). Dimuat di <head> base.html sehingga sudah
 * tersedia sebelum skrip inline halaman dijalankan.
 */

// Membaca nilai cookie, digunakan untuk mengambil token CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Mengubah karakter khusus HTML menjadi entity agar ditampilkan sebagai teks.
// '&' diganti paling awal supaya entity hasil penggantian lain tidak ikut diubah.
function escapeHtml(value) {
    return String(value ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
}

// Escaping tidak menghalangi URL seperti "javascript:alert(1)" di atribut href.
// Fungsi ini hanya meloloskan URL http/https dan mengembalikan string kosong
// untuk skema lain, sebagai lapisan tambahan di samping validasi URLField.
function safeUrl(value) {
    if (!value) return '';
    try {
        const url = new URL(value, window.location.origin);
        return ['http:', 'https:'].includes(url.protocol) ? url.href : '';
    } catch (error) {
        return '';
    }
}
