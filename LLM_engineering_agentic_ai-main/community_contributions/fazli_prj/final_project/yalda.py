import turtle
import random

screen = turtle.Screen()
screen.setup(1000, 700)
screen.bgcolor("#1a0f2b")  # شب یلدایی
screen.title("شب یلدا")

t = turtle.Turtle()
t.speed(0)
t.hideturtle()

# ---------- توابع پایه ----------
def rect(x, y, w, h, color):
    t.penup()
    t.goto(x, y)
    t.pendown()
    t.color(color)
    t.begin_fill()
    for _ in range(2):
        t.forward(w)
        t.right(90)
        t.forward(h)
        t.right(90)
    t.end_fill()

def circle(x, y, r, color):
    t.penup()
    t.goto(x, y - r)
    t.pendown()
    t.color(color)
    t.begin_fill()
    t.circle(r)
    t.end_fill()

# ---------- میز ----------
rect(-400, -100, 800, 200, "#7b3f00")

# ---------- هندوانه قاچ ----------
t.penup()
t.goto(-250, -50)
t.setheading(0)
t.pendown()
t.color("darkgreen", "red")
t.begin_fill()
t.circle(80, 180)
t.left(90)
t.forward(20)
t.left(90)
t.circle(100, 180)
t.end_fill()

# ---------- دانه‌های هندوانه ----------
for _ in range(10):
    circle(random.randint(-260, -170), random.randint(-40, 20), 3, "black")

# ---------- کدو حلوایی ----------
circle(0, -40, 50, "orange")
rect(-10, 10, 20, 25, "green")

# ---------- انار ----------
circle(180, -40, 35, "darkred")
rect(170, 5, 20, 15, "brown")

# ---------- آجیل ----------
for _ in range(12):
    circle(random.randint(-50, 50), random.randint(-80, -40), 6, "#d2b48c")

# ---------- کتاب ----------
rect(300, -60, 120, 80, "#3b4cc0")
t.penup()
t.goto(310, -20)
t.color("white")
t.write("غزلیات\nحافظ", font=("Arial", 12, "bold"))

# ---------- ریسه‌های رنگی ----------
lights = []
colors = ["red", "yellow", "green", "cyan", "magenta"]

for x in range(-450, 451, 60):
    light = turtle.Turtle()
    light.hideturtle()
    light.penup()
    light.goto(x, 250)
    light.shape("circle")
    light.shapesize(0.8)
    light.color(random.choice(colors))
    light.showturtle()
    lights.append(light)

def blink():
    for light in lights:
        light.color(random.choice(colors))
    screen.ontimer(blink, 500)

blink()

screen.mainloop()
