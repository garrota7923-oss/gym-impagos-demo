"""Anade reservas y enlaces personales a la base de datos (se ejecuta una vez)."""
import random, secrets, sqlite3
from datetime import date, timedelta

BD = "negocios.db"
c = sqlite3.connect(BD)
cols = [r[1] for r in c.execute("PRAGMA table_info(cliente)")]
if "token" not in cols:
    c.execute("ALTER TABLE cliente ADD COLUMN token TEXT")
    c.execute("CREATE UNIQUE INDEX ix_token ON cliente(token)")
c.executescript("""
CREATE TABLE IF NOT EXISTS reserva (
    id INTEGER PRIMARY KEY,
    negocio_id INTEGER NOT NULL REFERENCES negocio(id),
    cliente_id INTEGER NOT NULL REFERENCES cliente(id),
    actividad_id INTEGER NOT NULL REFERENCES actividad(id),
    fecha TEXT NOT NULL,
    estado TEXT NOT NULL,
    creada_en TEXT NOT NULL,
    UNIQUE (cliente_id, actividad_id, fecha));
CREATE INDEX IF NOT EXISTS ix_reserva ON reserva(negocio_id, actividad_id, fecha, estado);
""")
for (cid,) in c.execute("SELECT id FROM cliente WHERE token IS NULL").fetchall():
    c.execute("UPDATE cliente SET token=? WHERE id=?", (secrets.token_urlsafe(8), cid))

random.seed(9)
hoy = date.today()
acts = c.execute("SELECT id, negocio_id, dias, aforo FROM actividad").fetchall()
for aid, nid, dias, aforo in acts:
    socios = [r[0] for r in c.execute(
        """SELECT c.id FROM cliente c JOIN membresia m ON m.cliente_id=c.id
           WHERE c.negocio_id=? AND m.estado='activa'""", (nid,))]
    dias = [int(x) for x in dias.split(",")]
    for k in range(0, 6):
        d = hoy + timedelta(days=k)
        if d.weekday() not in dias:
            continue
        n = min(len(socios), aforo, int(aforo * random.choice([0.2, 0.4, 0.6, 0.85, 1.0])))
        for cid in random.sample(socios, n):
            c.execute("""INSERT OR IGNORE INTO reserva (negocio_id, cliente_id, actividad_id, fecha, estado, creada_en)
                         VALUES (?,?,?,?,'reservada',?)""", (nid, cid, aid, d.isoformat(), hoy.isoformat()))
c.commit()
n = c.execute("SELECT COUNT(*) FROM reserva").fetchone()[0]
print(f"Listo: enlaces personales creados y {n} reservas de ejemplo")