import tkinter as tk
from tkinter import ttk
import random
import math

GRAVITY = 9.81
TIME_STEP = 0.016
DRAG = 1
CUBE_SIZE = 40
BREAK_SPEED = 9.5
PPM = 50
MAGNET_R = 200
MAGNET_S = 0.08
gravity_on = True

MATERIALS = {
    "Wood": {"color": "#a0662b", "density": 0.6, "bounce": 0.35, "friction": 0.85, "break": False},
    "Metal": {"color": "#9aa0a6", "density": 1.6, "bounce": 0.15, "friction": 0.90, "break": False},
    "Ice": {"color": "#9fdfff", "density": 0.9, "bounce": 0.55, "friction": 0.98, "break": True},
    "Magnet": {"color": "#f13a3a", "density": 1.67, "bounce": 0.10, "friction": 0.95, "break": False},
    "Rubber": {"color": "#ff5b5b", "density": 0.5, "bounce": 0.85, "friction": 0.80, "break": False},
    "Glass": {"color": "#d7f0ff", "density": 0.7, "bounce": 0.60, "friction": 0.95, "break": True},
    "Lava (broken)": {"color": "#f1581b", "density": 0.7, "bounce": 0.60, "friction": 0.95, "break": False},
}

root = tk.Tk()
root.title("Cube Simulator")

width = 1440
height = 720

cubes = []
shards = []

dragged_cube = None
last_mouse_x = 0
last_mouse_y = 0
throw_x = 0
throw_y = 0


def cre_cube(x, y, material):
    data = MATERIALS[material]

    cube = {
        "x": x,
        "y": y,
        "material": material,
        "size": CUBE_SIZE,
        "color": data["color"],
        "density": data["density"],
        "bounce": data["bounce"],
        "friction": data["friction"],
        "can_break": data["break"],
        "mass": data["density"] * CUBE_SIZE * CUBE_SIZE / 1000,
        "vx": random.uniform(-2, 2),
        "vy": 0,
        "held": False,
        "broken": False,
        "squish": 0
    }

    cube["rect"] = canvas.create_rectangle(
        x, y, x + CUBE_SIZE, y + CUBE_SIZE,
        fill=cube["color"], outline="black", width=2
    )

    cube["label"] = canvas.create_text(
        x + CUBE_SIZE / 2, y + CUBE_SIZE / 2,
        text=material[0], fill="black",
        font=("Arial", 10, "bold")
    )

    return cube


def center(cube):
    return (
        cube["x"] + cube["size"] / 2,
        cube["y"] + cube["size"] / 2
    )


def speed(cube):
    return math.hypot(cube["vx"], cube["vy"])


def has(cube, x, y):
    return (
        cube["x"] <= x <= cube["x"] + cube["size"]
        and cube["y"] <= y <= cube["y"] + cube["size"]
    )


def draw_cube(cube):
    extra = cube["squish"] / 2

    left = cube["x"] - extra
    right = cube["x"] + cube["size"] + extra
    top = cube["y"] + cube["squish"]
    bottom = cube["y"] + cube["size"]

    canvas.coords(cube["rect"], left, top, right, bottom)
    canvas.coords(
        cube["label"],
        (left + right) / 2,
        (top + bottom) / 2
    )


def del_cube(cube):
    canvas.delete(cube["rect"])
    canvas.delete(cube["label"])


def upd_cube(cube):
    if cube["held"]:
        return

    if gravity_on:
        cube["vy"] += GRAVITY * TIME_STEP
    
    cube["vx"] *= DRAG
    cube["vy"] *= DRAG

    cube["x"] += cube["vx"] * PPM * TIME_STEP
    cube["y"] += cube["vy"] * PPM * TIME_STEP

    floor = height - cube["size"]

    if cube["y"] >= floor:
        cube["y"] = floor

        if cube["can_break"] and speed(cube) > BREAK_SPEED:
            cube["broken"] = True
            return

        if abs(cube["vy"]) > 0.5:
            cube["vy"] = -cube["vy"] * cube["bounce"]
        else:
            cube["vy"] = 0

        cube["vx"] *= cube["friction"]

    if cube["x"] < 0:
        if cube["can_break"] and speed(cube) > BREAK_SPEED:
            cube["broken"] = True
            return

        cube["x"] = 0
        cube["vx"] = -cube["vx"] * cube["bounce"]

    elif cube["x"] + cube["size"] > width:
        if cube["can_break"] and speed(cube) > BREAK_SPEED:
            cube["broken"] = True
            return

        cube["x"] = width - cube["size"]
        cube["vx"] = -cube["vx"] * cube["bounce"]

    if cube["y"] < 0:
        cube["y"] = 0
        cube["vy"] = -cube["vy"] * cube["bounce"]

    draw_cube(cube)


def cre_shard(x, y, color, vx, vy):
    size = random.randint(4, 10)
    points = []

    for _ in range(3):
        points.append(x + random.uniform(-size, size))
        points.append(y + random.uniform(-size, size))

    return {
        "x": x,
        "y": y,
        "vx": vx,
        "vy": vy,
        "life": 60,
        "shape": canvas.create_polygon(
            points,
            fill=color,
            outline="black"
        )
    }


def upd_shard(shard):
    if gravity_on:
        shard["vy"] += GRAVITY
    
    shard["x"] += shard["vx"]
    shard["y"] += shard["vy"]
    shard["life"] -= 1

    if shard["y"] > height:
        shard["vy"] = 0

    canvas.move(
        shard["shape"],
        shard["vx"],
        shard["vy"]
    )


def collide(first, second):
    ax, ay = center(first)
    bx, by = center(second)

    dx = bx - ax
    dy = by - ay
    distance = math.hypot(dx, dy)

    if distance == 0:
        distance = 0.01

    minimum_distance = first["size"] * 0.9

    if distance >= minimum_distance:
        return

    normal_x = dx / distance
    normal_y = dy / distance
    push = (minimum_distance - distance) / 2

    if not first["held"]:
        first["x"] -= normal_x * push
        first["y"] -= normal_y * push

    if not second["held"]:
        second["x"] += normal_x * push
        second["y"] += normal_y * push

    rvx = second["vx"] - first["vx"]
    rvy = second["vy"] - first["vy"]

    rv = rvx * normal_x + rvy * normal_y

    if rv >= 0:
        return

    bounce = (first["bounce"] + second["bounce"]) / 2

    impulse = (
        -(1 + bounce) * rv
        / (first["mass"] + second["mass"])
    )

    if not first["held"]:
        first["vx"] -= impulse * second["mass"] * normal_x
        first["vy"] -= impulse * second["mass"] * normal_y

    if not second["held"]:
        second["vx"] += impulse * first["mass"] * normal_x
        second["vy"] += impulse * first["mass"] * normal_y


def spawn_cube():
    material = selected_material.get()

    x = random.randint(
        0,
        max(0, width - CUBE_SIZE)
    )

    cubes.append(cre_cube(x, 0, material))
    next_counter()


def clear():
    for cube in cubes:
        del_cube(cube)

    for shard in shards:
        canvas.delete(shard["shape"])

    cubes.clear()
    shards.clear()

    next_counter()


def next_counter():
    counter.config(text=f"Cubes: {len(cubes)}")


def exit_cube(cube):
    x, y = center(cube)
    cube_speed = speed(cube)

    for _ in range(8):
        vx = random.uniform(-1, 1) * cube_speed * 0.5
        vy = random.uniform(-1, 1) * cube_speed * 0.5 - 2

        shards.append(
            cre_shard(
                x,
                y,
                cube["color"],
                vx,
                vy
            )
        )

    del_cube(cube)


def next_rubber():
    for cube in cubes:
        if cube["material"] != "Rubber":
            continue

        metal_cube = None

        for other in cubes:
            if other is cube or other["material"] != "Metal":
                continue

            touching = (
                other["x"] < cube["x"] + cube["size"]
                and other["x"] + other["size"] > cube["x"]
            )

            if not touching:
                continue

            gap = other["y"] + other["size"] - cube["y"]

            if 0 <= gap <= 10:
                metal_cube = other
                break

        if metal_cube:
            target = min(
                cube["size"] * 0.35,
                metal_cube["mass"] * 6
            )
        else:
            target = 0

        cube["squish"] += (
            target - cube["squish"]
        ) * 0.3

        if cube["squish"] < 0.05:
            cube["squish"] = 0

        draw_cube(cube)


def resize(event):
    global width, height

    width = event.width
    height = event.height


def mouse_down(event):
    global dragged_cube
    global last_mouse_x, last_mouse_y
    global throw_x, throw_y

    for cube in reversed(cubes):
        if has(cube, event.x, event.y):
            dragged_cube = cube
            cube["held"] = True

            last_mouse_x = event.x
            last_mouse_y = event.y
            throw_x = 0
            throw_y = 0
            return


def mouse_move(event):
    global last_mouse_x, last_mouse_y
    global throw_x, throw_y

    if dragged_cube is None:
        return

    dx = event.x - last_mouse_x
    dy = event.y - last_mouse_y

    dragged_cube["x"] += dx
    dragged_cube["y"] += dy

    throw_x = dx
    throw_y = dy

    last_mouse_x = event.x
    last_mouse_y = event.y

    draw_cube(dragged_cube)


def mouse_up(event):
    global dragged_cube

    if dragged_cube is None:
        return

    dragged_cube["vx"] = throw_x
    dragged_cube["vy"] = throw_y
    dragged_cube["held"] = False
    dragged_cube = None


def toggle_gravity():
    global gravity_on
    gravity_on = not gravity_on
    gravity_btn.config(text=f"Gravity: {'ON' if gravity_on else 'OFF'}")


def setup_controls():
    global selected_material
    global counter
    global gravity_btn

    top = tk.Frame(root)
    top.pack(fill="x", padx=8, pady=8)

    tk.Label(top, text="Material:").pack(side="left")

    selected_material = tk.StringVar(value="Wood")

    material_box = ttk.Combobox(
        top,
        textvariable=selected_material,
        values=list(MATERIALS),
        state="readonly",
        width=10
    )
    material_box.pack(side="left", padx=5)

    tk.Button(
        top,
        text="Spawn Cube",
        command=spawn_cube
    ).pack(side="left", padx=4)

    tk.Button(
        top,
        text="Clear",
        command=clear
    ).pack(side="left", padx=4)

    gravity_btn = tk.Button(
        top,
        text="Gravity: ON",
        command=toggle_gravity,
        bg="#90EE90" if gravity_on 
        else "#FFB6C6"
    )
    gravity_btn.pack(side="left", padx=4)

    counter = tk.Label(top, text="Cubes: 0")
    counter.pack(side="left", padx=12)


def setup_canvas():
    global canvas

    canvas = tk.Canvas(
        root,
        width=width,
        height=height,
        bg="#1e1e2e"
    )
    canvas.pack(padx=8, pady=(0, 8))

    canvas.bind("<Configure>", resize)
    canvas.bind("<ButtonPress-1>", mouse_down)
    canvas.bind("<B1-Motion>", mouse_move)
    canvas.bind("<ButtonRelease-1>", mouse_up)


GRID_SIZE = 100
grid = {}


def get_nearby_cubes(cube):
    cell_x = int(cube["x"] // GRID_SIZE)
    cell_y = int(cube["y"] // GRID_SIZE)
    nearby = []
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            key = (cell_x + dx, cell_y + dy)
            nearby.extend(grid.get(key, []))
    return nearby


def next_magnet():
    for magnet in cubes:
        if magnet["material"] != "Magnet":
            continue
        
        mx, my = center(magnet)
        
        for metal in cubes:
            if metal is magnet or metal["material"] != "Metal":
                continue
            
            mtx, mty = center(metal)
            dx = mx - mtx
            dy = my - mty
            distance = math.hypot(dx, dy)
            
            if distance > MAGNET_R or distance < 1:
                continue
            
            norm_x = dx / distance
            norm_y = dy / distance
            strength = MAGNET_S * (1 - distance / MAGNET_R)
            
            metal["vx"] += norm_x * strength
            metal["vy"] += norm_y * strength


def loop():
    global grid
    
    grid.clear()
    for cube in cubes:
        cell_x = int(cube["x"] // GRID_SIZE)
        cell_y = int(cube["y"] // GRID_SIZE)
        key = (cell_x, cell_y)
        if key not in grid:
            grid[key] = []
        grid[key].append(cube)
    
    for cube in cubes:
        upd_cube(cube)
    
    checked = set()
    for cube in cubes:
        nearby = get_nearby_cubes(cube)
        for other in nearby:
            pair = tuple(sorted([id(cube), id(other)]))
            if pair in checked or cube is other:
                continue
            checked.add(pair)
            collide(cube, other)
    
    next_rubber()
    next_magnet()
    
    for cube in cubes[:]:
        if cube["broken"]:
            exit_cube(cube)
            cubes.remove(cube)
    
    for shard in shards[:]:
        upd_shard(shard)
        if shard["life"] <= 0:
            canvas.delete(shard["shape"])
            shards.remove(shard)
    
    next_counter()
    root.after(16, loop)


def next_counter():
    if cubes:
        velocity = max(speed(cube) for cube in cubes)
    else:
        velocity = 0
 
    counter.config(
        text=f"Cubes: {len(cubes)}    Velocity: {velocity:.2f}. idk what to put here so HAPPY BIRTHDAY <3"
    )


setup_controls()
setup_canvas()
loop()

root.mainloop()
