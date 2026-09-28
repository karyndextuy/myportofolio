"""Aturan hak akses (otorisasi) untuk data portofolio.

Ada empat peran:

- Pengunjung (belum login): hanya membaca.
- Pengguna biasa: membaca dan memberi/membatalkan star.
- Editor (anggota grup ``Editor``, ditetapkan lewat Django Admin):
  hak pengguna biasa ditambah mengubah data, tanpa membuat atau menghapus.
- Pemilik portofolio (superuser): membuat, mengubah, dan menghapus data.

Fungsi di sini dipakai di views (pemeriksaan sisi server) dan, lewat
``main.context_processors.user_roles``, di template untuk menyembunyikan
tombol yang tidak boleh dipakai.
"""

EDITOR_GROUP_NAME = "Editor"


def is_editor(user):
    """True jika ``user`` sudah login dan tergabung di grup Editor."""
    return user.is_authenticated and user.groups.filter(name=EDITOR_GROUP_NAME).exists()


def can_create(user):
    """Hanya pemilik portofolio yang boleh menambah data."""
    return user.is_superuser


def can_update(user):
    """Pemilik portofolio dan Editor boleh mengubah data."""
    return user.is_superuser or is_editor(user)


def can_delete(user):
    """Hanya pemilik portofolio yang boleh menghapus data."""
    return user.is_superuser
