"""
Mundosim Facturador - App Web
Backend Flask con SQLite para gestion de comprobantes ARCA
Soporta Factura A (tipo 1) y Factura B (tipo 6)
"""

from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash
from functools import wraps
import sqlite3
import json
import os
import csv
import io
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "mundosim-secret-2024")

DB_PATH = os.environ.get("DB_PATH", "facturador.db")

USUARIOS = {
    "mendoza": {
        "password": os.environ.get("PASS_MENDOZA", "mendoza123"),
        "sucursal": "Mendoza",
        "punto_venta": int(os.environ.get("PV_MENDOZA", "1")),
    },
    "sanjuan": {
        "password": os.environ.get("PASS_SANJUAN", "sanjuan123"),
        "sucursal": "San Juan",
        "punto_venta": int(os.environ.get("PV_SANJUAN", "2")),
    },
    "admin": {
        "password": os.environ.get("PASS_ADMIN", "admin2024"),
        "sucursal": "Administracion",
        "punto_venta": None,
    },
}

TIPOS_COMPROBANTE = {
    "A": {"codigo": 1,  "nombre": "Factura A", "iva": True},
    "B": {"codigo": 6,  "nombre": "Factura B", "iva": False},
}

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS comprobantes (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                numero       INTEGER,
                tipo         TEXT,
                punto_venta  INTEGER,
                sucursal     TEXT,
                fecha        TEXT,
                destinatario TEXT,
                doc_tipo     INTEGER,
                doc_nro      TEXT,
                neto         REAL,
                iva          REAL,
                monto        REAL,
                cae          TEXT,
                cae_vto      TEXT,
                estado       TEXT,
                error        TEXT,
                usuario      TEXT,
                created_at   TEXT DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

init_db()

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated

@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        usuario = request.form.get("usuario", "").lower()
        password = request.form.get("password", "")
        if usuario in USUARIOS and USUARIOS[usuario]["password"] == password:
            session["usuario"] = usuario
            session["sucursal"] = USUARIOS[usuario]["sucursal"]
            session["punto_venta"] = USUARIOS[usuario]["punto_venta"]
            return redirect(url_for("dashboard"))
        error = "Usuario o contrasena incorrectos"
    return render_template("login.html", error=error)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/")
@login_required
def dashboard():
    with get_db() as conn:
        if session["usuario"] == "admin":
            rows = conn.execute(
                "SELECT * FROM comprobantes ORDER BY created_at DESC LIMIT 100"
            ).fetchall()
            total_mes = conn.execute("""
                SELECT COALESCE(SUM(monto),0) FROM comprobantes
                WHERE estado='APROBADO'
                AND strftime('%Y-%m', fecha) = strftime('%Y-%m', 'now')
            """).fetchone()[0]
            cant_mes = conn.execute("""
                SELECT COUNT(*) FROM comprobantes
                WHERE estado='APROBADO'
                AND strftime('%Y-%m', fecha) = strftime('%Y-%m', 'now')
            """).fetchone()[0]
        else:
            sucursal = session["sucursal"]
            rows = conn.execute(
                "SELECT * FROM comprobantes WHERE sucursal=? ORDER BY created_at DESC LIMIT 100",
                (sucursal,)
            ).fetchall()
            total_mes = conn.execute("""
                SELECT COALESCE(SUM(monto),0) FROM comprobantes
                WHERE sucursal=? AND estado='APROBADO'
                AND strftime('%Y-%m', fecha) = strftime('%Y-%m', 'now')
            """, (sucursal,)).fetchone()[0]
            cant_mes = conn.execute("""
                SELECT COUNT(*) FROM comprobantes
                WHERE sucursal=? AND estado='APROBADO'
                AND strftime('%Y-%m', fecha) = strftime('%Y-%m', 'now')
            """, (sucursal,)).fetchone()[0]

    return render_template("dashboard.html",
        comprobantes=rows,
        total_mes=total_mes,
        cant_mes=cant_mes,
        usuario=session["usuario"],
        sucursal=session["sucursal"],
    )

@app.route("/emitir", methods=["GET", "POST"])
@login_required
def emitir():
    if request.method == "POST":
        tipo = request.form.get("tipo", "B")
        monto_total = float(request.form.get("monto", 0))

        if tipo == "A":
            neto = round(monto_total / 1.21,
