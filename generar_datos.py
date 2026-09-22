import csv, random
from datetime import date, time, timedelta
from openpyxl import Workbook

random.seed(11)
NOMBRES = ["Lucia","Hugo","Martina","Pablo","Sofia","Alvaro","Carla","Daniel","Paula","Javier",
           "Irene","Sergio","Nerea","Adrian","Laura","Marcos","Elena","Ruben","Noelia","Ivan",
           "Sara","Mario","Alba","Victor","Claudia","Oscar","Raquel","Diego","Ines","Bruno"]
LETRAS = "ABCDEGHLMPRST"
HORAS = [time(9,30), time(10,45), time(12,0), time(16,0), time(17,15), time(18,30), time(19,45), time(21,0)]
PESO = [0.6, 0.35, 0.3, 0.45, 0.75, 1.0, 0.8, 0.55]
PLAZAS, CUOTA = 14, 65
DIAS = ["LUNES","MARTES","MIERCOLES","JUEVES","VIERNES"]
MESES = {7: "JULIO 2026", 8: "AGOSTO 2026", 9: "SEPTIEMBRE 26"}
HOY = date(2026, 9, 17)
usados = set()

def nombre_nuevo():
    while True:
        n = f"{random.choice(NOMBRES)} {random.choice(LETRAS)}"
        if n not in usados:
            usados.add(n)
            return n

socios = [{"nombre": nombre_nuevo(), "hora": random.choices(range(8), PESO)[0],
           "freq": random.choice([2, 2, 3, 3, 4]), "desde": date(2026, 7, 1), "hasta": None}
          for _ in range(55)]
for s in random.sample(socios, 7):
    s["hasta"] = date(2026, 7, 1) + timedelta(days=random.randint(25, 75))

wb = Workbook()
wb.remove(wb.active)
for mes, titulo in MESES.items():
    ws = wb.create_sheet(titulo)
    ws.append(["BOXEO", titulo.split()[0]])
    d = date(2026, mes, 1)
    while d.month == mes:
        if d.weekday() < 5:
            clases = {h: [] for h in range(8)}
            if d <= HOY:
                for s in socios:
                    if s["desde"] <= d and (s["hasta"] is None or d < s["hasta"]) \
                            and random.random() < s["freq"] / 5:
                        h = s["hora"] if random.random() < 0.75 else random.choices(range(8), PESO)[0]
                        if len(clases[h]) < PLAZAS:
                            clases[h].append(s["nombre"])
                for _ in range(random.choice([0, 0, 1, 1, 2])):
                    h = random.choices(range(8), PESO)[0]
                    if len(clases[h]) < PLAZAS:
                        n = nombre_nuevo()
                        clases[h].append(f"{n} CP")
                        if random.random() < 0.4:
                            socios.append({"nombre": n, "hora": h, "freq": random.choice([2, 3]),
                                           "desde": d + timedelta(days=5), "hasta": None})
            ws.append([f"{DIAS[d.weekday()]} {d.day}"])
            ws.append(["Boxeo"] * 8)
            ws.append(HORAS)
            for i in range(PLAZAS):
                ws.append([f"{i+1}. {clases[h][i]}" if i < len(clases[h]) else f"{i+1}."
                           for h in range(8)])
        d += timedelta(days=1)
wb.save("horarios_demo.xlsx")

pagos = []
for s in socios:
    for mes in MESES:
        inicio = date(2026, mes, 1)
        if s["desde"] > date(2026, mes, 28) or (s["hasta"] and s["hasta"] < inicio):
            continue
        dia_pago = max(inicio, s["desde"]) + timedelta(days=random.randint(0, 9))
        if dia_pago > HOY or random.random() < 0.08:
            continue
        pagos.append([s["nombre"], f"2026-{mes:02d}", dia_pago.isoformat(), CUOTA,
                      random.choice(["Bizum", "Efectivo", "Tarjeta", "Bizum"])])
with open("pagos.csv", "w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["nombre", "mes", "fecha_pago", "importe", "metodo"])
    w.writerows(pagos)
print(f"Listo: horarios_demo.xlsx y pagos.csv ({len(socios)} socios, {len(pagos)} pagos)")
