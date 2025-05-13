import mysql.connector
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
import questionary
import sys

console = Console()

def koneksi_mysql(db=None):
    try:
        # Koneksi ke MySQL
        conn = mysql.connector.connect(
            host="localhost",
            user="root",
            password="",
            database=db if db else None
        )
        return conn
    except mysql.connector.Error as err:
        console.print(f"[red]Gagal konek ke database: {err}[/red]")
        sys.exit()

def pilih_database():
    conn = koneksi_mysql()
    cursor = conn.cursor()

    while True:
        cursor.execute("SHOW DATABASES")
        dbs = [db[0] for db in cursor.fetchall() if db[0] not in ["information_schema", "mysql", "performance_schema", "sys"]]

        pilihan = questionary.select(
            "Pilih atau buat database:",
            choices=["📦 Buat Database Baru"] + dbs + ["❌ Keluar Aplikasi"]
        ).ask()

        if pilihan == "📦 Buat Database Baru":
            nama_baru = questionary.text("Masukkan nama database baru:").ask()
            if nama_baru:
                try:
                    cursor.execute(f"CREATE DATABASE {nama_baru}")
                    console.print(f"[green]Database '{nama_baru}' berhasil dibuat.[/green]")
                    return nama_baru
                except mysql.connector.Error as err:
                    console.print(f"[red]Gagal membuat database: {err}[/red]")
            else:
                console.print("[red]Nama database tidak boleh kosong.[/red]")
        elif pilihan == "❌ Keluar Aplikasi":
            console.print("[cyan]Sampai jumpa![/cyan]")
            sys.exit()
        else:
            return pilihan

def tampilkan_hasil(cursor):
    if cursor.description:
        columns = [desc[0] for desc in cursor.description]
        results = cursor.fetchall()
        table = Table(show_header=True, header_style="bold cyan")
        for col in columns:
            table.add_column(col)
        for row in results:
            table.add_row(*[str(col) for col in row])
        console.print(table)
    else:
        console.print(f"[green]Query berhasil dijalankan. Baris yang terpengaruh: {cursor.rowcount}[/green]")

def tampilkan_data_tabel(cursor):
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    if tables:
        table = Table(title="Daftar Tabel", show_header=True, header_style="bold cyan")
        table.add_column("No.", justify="center", style="cyan")
        table.add_column("Nama Tabel", style="magenta")
        for idx, table_name in enumerate(tables, start=1):
            table.add_row(str(idx), table_name[0])
        console.print(table)

        tabel = questionary.select(
            "Pilih tabel yang ingin ditampilkan:",
            choices=[table_name[0] for table_name in tables]
        ).ask()

        cursor.execute(f"DESCRIBE {tabel}")
        kolom = cursor.fetchall()
        if kolom:
            table = Table(title=f"Struktur Tabel: {tabel}", show_header=True, header_style="bold cyan")
            table.add_column("Field", style="magenta")
            table.add_column("Type", style="cyan")
            table.add_column("Null", style="green")
            table.add_column("Key", style="yellow")
            table.add_column("Default", style="blue")
            table.add_column("Extra", style="red")

            for row in kolom:
                table.add_row(row[0], row[1], row[2], row[3], str(row[4]), row[5])

            console.print(table)
            cursor.execute(f"SELECT * FROM {tabel}")
            tampilkan_hasil(cursor)
        else:
            console.print(f"[red]Tabel '{tabel}' tidak ditemukan.[/red]")
    else:
        console.print("[red]Tidak ada tabel dalam database ini.[/red]")

def jalankan_query(cursor, conn):
    console.print(Panel("Ketik query SQL-mu. Akhiri dengan baris kosong lalu tekan ENTER dua kali.", style="bold yellow"))
    lines = []
    while True:
        line = questionary.text("SQL> ").ask()
        if line.strip() == "":
            break
        lines.append(line)
    query = "\n".join(lines).strip()
    if not query:
        console.print("[red]Query kosong. Dibatalkan.[/red]")
        return

    konfirmasi = questionary.confirm("Yakin ingin menjalankan query ini?").ask()
    if not konfirmasi:
        console.print("[yellow]Dibatalkan oleh user.[/yellow]")
        return

    try:
        cursor.execute(query)
        if query.lower().startswith(("insert", "update", "delete", "alter", "drop", "create")):
            conn.commit()
        tampilkan_hasil(cursor)
    except mysql.connector.Error as err:
        console.print(f"[red]Terjadi kesalahan: {err}[/red]")

def menu(cursor, conn):
    while True:
        pilihan = questionary.select(
            "Apa yang ingin kamu lakukan?",
            choices=[
                "💻 Jalankan Query SQL",
                "📂 Tampilkan Daftar Tabel",
                "🔙 Kembali ke Pilihan Database"
            ]
        ).ask()

        if pilihan == "💻 Jalankan Query SQL":
            jalankan_query(cursor, conn)
        elif pilihan == "📂 Tampilkan Daftar Tabel":
            tampilkan_data_tabel(cursor)
        else:
            break

def main():
    while True:
        db_terpilih = pilih_database()
        conn = koneksi_mysql(db_terpilih)
        cursor = conn.cursor()
        console.print(f"[bold green]Terhubung ke database:[/] [cyan]{db_terpilih}[/cyan]")
        menu(cursor, conn)

main()
