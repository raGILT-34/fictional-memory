import math
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.ticker import FuncFormatter
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

def ambil_data(nilai):
    # pengecekan input
    while nilai <= 0:
        print("Nilai ditolak, ulangi!")
        nilai = int(input("Masukkan nilai kembali: "))

    return nilai

def gerak(alas, perpindahan, jarak, kedalaman, periode):
    # rumus yang digunakan
    M0 = 3 * 10 **(10) * (alas * 10 **(6)) * perpindahan  # momen seismik
    Mw = (2/3) * (math.log10(M0) - 9.1) # magnitudo momen
    r_hipo = math.sqrt(jarak**2 + kedalaman**2) # jarak hiposenter alat
    PGA = (5 * 10 ** (0.61 * Mw - (1.66 + (3.6/r_hipo)) * math.log10(r_hipo) + 0.167 - (1.83/r_hipo))) / math.sqrt(periode) # PGA

    return M0, Mw, PGA, r_hipo

def panjang_bagus(x):
    """Pilih panjang 'bulat' (1, 2, 5 x 10^n) <= x untuk scale bar."""
    pangkat = 10 ** np.floor(np.log10(x))
    for m in (5, 2, 1):
        if m * pangkat <= x:
            return m * pangkat
    return pangkat

def gambar(PGA, periode, luas, perpindahan, kedalaman, pembesaran=5000):
    # Validasi Input
    if PGA < 0:
        raise ValueError("PGA tidak boleh negatif.")
    if periode <= 0 or luas <= 0 or perpindahan <= 0 or kedalaman <= 0:
        raise ValueError("periode, luas, perpindahan, kedalaman harus > 0.")

    # 1. Konversi ke satuan SI (meter)
    PGA_g = PGA / 980          # gal -> g
    PGA_ms2 = PGA / 100        # gal -> m/s^2
    sisi = np.sqrt(luas * 1e6)       # m
    dalam = kedalaman * 1e3          # m

    # 2. Skala spasial (isotropik)
    UKURAN_MODEL = 4.0                        # dimensi terbesar di model
    skala = UKURAN_MODEL / max(sisi, dalam)   # satuan model per meter
    s2 = sisi / 2 * skala                     # setengah sisi area (model)
    H = dalam * skala                         # tinggi blok (model)

    if max(sisi, dalam) >= 1000:
        div, sat = 1000, "km"
    else:
        div, sat = 1, "m"

    # 3. Skala perpindahan
    if pembesaran is None:  # otomatis: amplitudo visual = 15% sisi area
        pembesaran = max(1.0, 0.15 * sisi / perpindahan)
    amplitudo = perpindahan * skala * pembesaran    # satuan model

    # Cek konsistensi: d = a / w^2 untuk gerak harmonik
    omega = 2 * np.pi / periode
    d_pga = PGA_ms2 / omega**2
    print(f"Skala model        : 1 satuan = {1/skala/div:.3g} {sat}")
    print(f"Pembesaran         : {pembesaran:,.0f}x")
    print(f"Perpindahan input  : {perpindahan:.4f} m")
    print(f"Perpindahan dr PGA : {d_pga:.4f} m (a/w^2)")
    print(f"PGA                : {PGA_g:.3f} g")

    FREKUENSI = 1 / periode
    DURASI, FPS = 6, 30

    # 4. Pembuat balok
    def buat_balok(x1, x2, y1, y2, z1, z2):
        t = [[x1, y1, z1], [x2, y1, z1], [x2, y2, z1], [x1, y2, z1],
             [x1, y1, z2], [x2, y1, z2], [x2, y2, z2], [x1, y2, z2]]
        sisi_idx = [[0, 1, 2, 3], [4, 5, 6, 7], [0, 1, 5, 4],
                    [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]]
        return [[t[i] for i in s] for s in sisi_idx]

    # 5. Bidang patahan & blok
    fig = plt.figure(figsize=(9, 7))
    ax = fig.add_subplot(111, projection="3d")

    Y, Z = np.meshgrid(np.linspace(-s2, s2, 2), np.linspace(0, H, 2))
    ax.plot_surface(np.zeros_like(Y), Y, Z, color="red", alpha=0.3)

    blok_kiri = Poly3DCollection(buat_balok(-s2, 0, -s2, s2, 0, H),
                                 facecolor="steelblue", edgecolor="black", alpha=0.85)
    blok_kanan = Poly3DCollection(buat_balok(0, s2, -s2, s2, 0, H),
                                  facecolor="orange", edgecolor="black", alpha=0.85)
    ax.add_collection3d(blok_kiri)
    ax.add_collection3d(blok_kanan)

    # 6. Tampilan + label sumbu dalam satuan nyata
    lim = 1.3 * s2
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_zlim(0, H)
    ax.set_box_aspect((2 * lim, 2 * lim, H))   # proporsi = skala nyata

    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v/skala/div:.3g}"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v/skala/div:.3g}"))
    ax.zaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{(H - v)/skala/div:.3g}"))  # kedalaman

    ax.set_xlabel(f"X - tegak lurus patahan ({sat})")
    ax.set_ylabel(f"Y - sepanjang patahan ({sat})")
    ax.set_zlabel(f"Kedalaman ({sat})")
    ax.set_title("Animasi Pergeseran Bidang Patahan")

    # 7. Scale bar
    sb = panjang_bagus(0.3 * sisi)
    y0 = -1.2 * s2
    ax.plot([-s2, -s2 + sb * skala], [y0, y0], [0, 0], color="k", lw=4)
    ax.text(-s2 + sb * skala / 2, y0, 0, f"{sb/div:g} {sat}", ha="center")

    # 8. Kotak informasi
    info = (f"Luas area   : {luas:g} km²\n"
            f"Kedalaman   : {kedalaman:g} km\n"
            f"PGA         : {PGA_g:.3f} g\n"
            f"Periode     : {periode} s\n"
            f"Perpindahan : {perpindahan:g} m\n"
            f"Pembesaran  : {pembesaran:,.0f}x (perpindahan)")
    ax.text2D(0.02, 0.95, info, transform=ax.transAxes, va="top",
              fontsize=9, family="monospace",
              bbox=dict(boxstyle="round", facecolor="white", alpha=0.8))

    # 9. Animasi 
    jumlah_frame = DURASI * FPS
    waktu = np.linspace(0, DURASI, jumlah_frame)

    def update(frame):
        d = amplitudo * np.sin(2 * np.pi * FREKUENSI * waktu[frame])
        gk, gn = d / 2, -d / 2
        blok_kiri.set_verts(buat_balok(-s2, 0, -s2 + gk, s2 + gk, 0, H))
        blok_kanan.set_verts(buat_balok(0, s2, -s2 + gn, s2 + gn, 0, H))
        return blok_kiri, blok_kanan

    animasi = FuncAnimation(fig, update, frames=jumlah_frame,
                            interval=1000 / FPS, blit=False)
    plt.show()

def status(PGA):
    # klasifikasi status gempa
    if PGA < 2.9 :
        print(f"Skala MMI               : I-II")
        print(f"Skala SIG BMKG          : I")
        print(f"Deskripsi               : Tidak Dirasakan")
    elif PGA <= 88:
        print(f"Skala MMI               : III-V")
        print(f"Skala SIG BMKG          : II")
        print(f"Deskripsi               : Dirasakan")
    elif PGA <= 167:
        print(f"Skala MMI               : VI")
        print(f"Skala SIG BMKG          : III")
        print(f"Deskripsi               : Kerusakan Ringan")
    elif PGA <= 564:
        print(f"Skala MMI               : VII-VII")
        print(f"Skala SIG BMKG          : IV")
        print(f"'Deskripsi              : Kerusakan Sedang")
    else:
        print(f"'Skala MMI              : IX-XII")
        print(f"Skala SIG BMKG          : V")
        print(f"Deskripsi               : Kerusakan Berat")
    
def main():
    print("=" * 50)
    print("PROGRAM KLASIFIKASI GEMPA".center(50))
    print("=" * 50)
    print("Masukkan Data Gempa")
    # input
    A = float(input("Masukkan nilai luas bidang patahan yang mengalami pergeseran (km^2) : "))
    A = ambil_data(A)

    D = float(input("Masukkan nilai rata-rata perpindahan atau pergeseran batuan (m) : "))
    D = ambil_data(D)

    T = float(input("Masukkan nilai periode dominan tanah [0.21 - 5.17] (s) : "))
    T = ambil_data(T) 

    R = float(input("Masukkan jarak episenter (km) : "))
    R = ambil_data(R)

    K = float(input("Masukkan kedalaman (km) : "))
    K = ambil_data(K)

    # pengolahan data
    m , M, PGA, r_hipo = gerak(A, D, R, K, T)

    # output
    print()
    print("=" * 50)
    print("HASIL KLASIFIKASI".center(50))
    print("=" * 50)
    print(f"Momen Seismik                  : {m:.3e} N.m ")
    print(f"Magnitudo Momen                : {M:.2f} Mw ")
    print(f"Percepatan Tanah (PGA)         : {PGA:.2f} gal / {PGA/980:.2f} g")
    print(f"Jarak hiposenter               : {r_hipo:.1f} km")
    print()
    print("=" * 50)
    print("STATUS".center(50))
    print("=" * 50)
    status(PGA)
    print()
    print("=" * 50)
    print("DESKRIPSI ILUSTRASI".center(50))
    print("=" * 50)
    gambar(PGA,T,A,D,K)

main()
