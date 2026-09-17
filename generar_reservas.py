import csv, random
from datetime import date, timedelta

random.seed(7)
NOMBRES = ["Lucia","Hugo","Martina","Pablo","Sofia","Alvaro","Carla","Daniel","Paula",
           "Javier","Irene","Sergio","Nerea","Adrian","Laura","Marcos","Elena","Ruben",
           "Noelia","Ivan","Sara","Mario","Alba","Victor","Claudia","Oscar"]
APELLIDOS = ["Garcia","Lopez","Martin","Sanchez","Perez","Gomez","Ruiz","Diaz","Moreno","Alvarez"]
HORAS = ["09:30","10:45","12:00","16:00","17:15","18:30","19:45","21:00"]
PESO_HORA = [0.6, 0.35, 0.3, 0.45, 0.75, 1.0, 0.8, 0.55]
AFORO = 14
DIAS = ["Lunes","Martes","Miercoles","Jueves","Viernes","Sabado"]
INICIO, FIN = date(2026, 7, 1), date(2026, 9, 30)

def nuevo_nombre(i):
    return f"{random.choice(NOMBRES)} {random.choice(APELLIDOS)[0]}. #{i}"

socios, sid = [], 1
for _ in range(60):
    socios.append({"id": sid, "nombre": nuevo_nombre(sid), "tipo": "socio",
                   "hora_fav": random.choices(range(8), PESO_HORA)[0],
                   "dias_semana": random.choice([2, 2, 3, 3, 4]),
                   "alta": INICIO, "baja": None})
    sid += 1
for s in random.sample(socios, 8):
    s["baja"] = INICIO + timedelta(days=random.randint(20, 80))

filas, pruebas = [], []
d = INICIO
while d <= FIN:
    if d.weekday() < 6:
        clases = {h: [] for h in range(8)}
        for s in socios:
            if s["alta"] <= d and (s["baja"] is None or d < s["baja"]):
                if random.random() < s["dias_semana"] / 6:
                    h = s["hora_fav"] if random.random() < 0.75 else random.choices(range(8), PESO_HORA)[0]
                    if len(clases[h]) < AFORO:
                        clases[h].append((s, "socio"))
        for _ in range(random.choice([0, 1, 1, 2])):
            h = random.choices(range(8), PESO_HORA)[0]
            if len(clases[h]) < AFORO:
                p = {"id": sid, "nombre": nuevo_nombre(sid), "tipo": "prueba",
                     "hora_fav": h, "dias_semana": random.choice([2, 3]),
                     "alta": None, "baja": None}
                sid += 1
                clases[h].append((p, "prueba"))
                pruebas.append((p, d))
                if random.random() < 0.35:
                    p["alta"] = d + timedelta(days=7)
                    socios.append(p)
        for h, lista in clases.items():
            for puesto, (s, tipo) in enumerate(lista, 1):
                filas.append([d.isoformat(), DIAS[d.weekday()], HORAS[h], puesto,
                              s["id"], s["nombre"], tipo])
    d += timedelta(days=1)

with open("reservas.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["fecha","dia","hora","puesto","socio_id","nombre","tipo_reserva"])
    w.writerows(filas)

convertidos = sum(1 for p, _ in pruebas if p["alta"])
print(f"Listo: reservas.csv con {len(filas)} reservas (jul-sep 2026)")
print(f"Clases de prueba: {len(pruebas)} | se apuntaron: {convertidos} ({convertidos/len(pruebas):.0%})")
