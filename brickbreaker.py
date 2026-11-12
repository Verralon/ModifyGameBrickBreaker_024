import tkinter as tk
import math
import random


class GameObject:
    def __init__(self, canvas, item):
        self.canvas = canvas
        self.item = item

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)

    def delete(self):
        self.canvas.delete(self.item)


class Ball(GameObject):
    def __init__(self, canvas, x, y):
        self.radius = 8
        self.dx = 5
        self.dy = -5
        self.speed = 7
        
        # Efek Glow / Bayangan Bola
        self.shadow = canvas.create_oval(
            x - self.radius - 2, y - self.radius - 2,
            x + self.radius + 2, y + self.radius + 2,
            fill='#1e293b', outline=''
        )
        item = canvas.create_oval(
            x - self.radius, y - self.radius,
            x + self.radius, y + self.radius,
            fill='#38bdf8', outline=''
        )
        super(Ball, self).__init__(canvas, item)

    def get_position(self):
        return self.canvas.coords(self.item)

    def move(self, x, y):
        self.canvas.move(self.item, x, y)
        self.canvas.move(self.shadow, x, y)

    def delete(self):
        self.canvas.delete(self.item)
        self.canvas.delete(self.shadow)

    def update(self):
        self.move(self.dx, self.speed * (self.dy / abs(self.dy) if self.dy != 0 else -1))
        coords = self.get_position()
        width = self.canvas.winfo_width()
        
        # Pantulan dinding kiri/kanan
        if coords[0] <= 15:
            self.dx = abs(self.dx)
        elif coords[2] >= width - 15:
            self.dx = -abs(self.dx)
            
        # Pantulan dinding atas
        if coords[1] <= 60:
            self.dy = abs(self.dy)

    def set_vector(self, dx, dy):
        length = math.hypot(dx, dy)
        if length == 0:
            return
        self.dx = (dx / length) * self.speed
        self.dy = (dy / length) * self.speed

    def collide(self, game_objects):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        
        hit_brick = False
        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()
                hit_brick = True

        if len(game_objects) > 1 or hit_brick:
            self.dy *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            if isinstance(game_object, Paddle):
                paddle_coords = game_object.get_position()
                paddle_center = (paddle_coords[0] + paddle_coords[2]) / 2
                offset = x - paddle_center
                # Pantulan dinamis berdasarkan posisi tumbukan pada paddle
                self.set_vector(offset * 0.15, -abs(self.dy))
            else:
                self.dy *= -1


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 110
        self.height = 12
        self.ball = None
        self.velocity = 0
        self.max_speed = 12
        
        item = canvas.create_rectangle(
            x - self.width / 2, y - self.height / 2,
            x + self.width / 2, y + self.height / 2,
            fill='#f43f5e', outline='', width=0
        )
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def update_position(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        
        # Batasan layar agar tidak keluar
        if coords[0] + self.velocity >= 15 and coords[2] + self.velocity <= width - 15:
            super(Paddle, self).move(self.velocity, 0)
            if self.ball is not None and self.ball.get_position()[3] < self.get_position()[1]:
                self.ball.move(self.velocity, 0)

    def move_to(self, new_x):
        """Membuat paddle bergerak sangat mulus mengikuti kursor mouse"""
        coords = self.get_position()
        width = self.canvas.winfo_width()
        current_center_x = (coords[0] + coords[2]) / 2
        offset = new_x - current_center_x
        
        if coords[0] + offset >= 15 and coords[2] + offset <= width - 15:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)


class Brick(GameObject):
    COLORS = {1: '#10b981', 2: '#f59e0b', 3: '#6366f1'}

    def __init__(self, canvas, x, y, hits):
        self.width = 68
        self.height = 18
        self.hits = hits
        color = Brick.COLORS[hits]
        
        item = canvas.create_rectangle(
            x - self.width / 2, y - self.height / 2,
            x + self.width / 2, y + self.height / 2,
            fill=color, outline='', tags='brick'
        )
        super(Brick, self).__init__(canvas, item)

    def hit(self):
        self.hits -= 1
        if self.hits == 0:
            self.delete()
        else:
            self.canvas.itemconfig(self.item, fill=Brick.COLORS[self.hits])


class Game(tk.Frame):
    def __init__(self, master):
        super(Game, self).__init__(master)
        self.lives = 3
        self.score = 0
        self.width = 650
        self.height = 480
        
        # Canvas dengan tema background gelap luar angkasa / modern night
        self.canvas = tk.Canvas(
            self, bg='#090d16',
            width=self.width, height=self.height,
            highlightthickness=0
        )
        self.canvas.pack()
        self.pack()

        # Generate background bintang-bintang statis agar ada tekstur latar belakang
        random.seed(42)
        for _ in range(40):
            bx = random.randint(20, self.width - 20)
            by = random.randint(60, self.height - 20)
            size = random.choice([1, 2])
            self.canvas.create_oval(bx, by, bx + size, by + size, fill='#1e293b', outline='')

        # Garis pembatas UI atas
        self.canvas.create_line(15, 50, self.width - 15, 50, fill='#1e293b', width=2)

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width / 2, 420)
        self.items[self.paddle.item] = self.paddle
        
        for r, hits_val in enumerate([3, 2, 1]):
            for x in range(25, self.width - 25, 75):
                self.add_brick(x + 35, 90 + (r * 25), hits_val)

        self.hud_score = None
        self.hud_lives = None
        self.center_text = None
        
        self.setup_game()
        self.canvas.focus_set()
        
        # Key bindings untuk gerakan fluid (tekan & lepas)
        self.canvas.bind('<KeyPress-Left>', lambda _: self.start_move(-1))
        self.canvas.bind('<KeyRelease-Left>', lambda _: self.stop_move())
        self.canvas.bind('<KeyPress-Right>', lambda _: self.start_move(1))
        self.canvas.bind('<KeyRelease-Right>', lambda _: self.stop_move())
        
        self.canvas.bind('<KeyPress-a>', lambda _: self.start_move(-1))
        self.canvas.bind('<KeyRelease-a>', lambda _: self.stop_move())
        self.canvas.bind('<KeyPress-d>', lambda _: self.start_move(1))
        self.canvas.bind('<KeyRelease-d>', lambda _: self.stop_move())
        
        # Mouse movement interaktif super mulus
        self.canvas.bind('<Motion>', lambda event: self.paddle.move_to(event.x))

    def start_move(self, direction):
        self.paddle.velocity = direction * self.paddle.max_speed

    def stop_move(self):
        self.paddle.velocity = 0

    def setup_game(self):
        self.add_ball()
        self.update_hud()
        self.center_text = self.canvas.create_text(
            self.width / 2, self.height / 2,
            text='PRESS SPACE TO START',
            font=('Segoe UI', 16, 'bold'),
            fill='#f8fafc'
        )
        self.canvas.bind('<space>', lambda _: self.start_game())

    def add_ball(self):
        if self.ball is not None:
            self.ball.delete()
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        self.ball = Ball(self.canvas, x, 405)
        self.paddle.set_ball(self.ball)

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits)
        self.items[brick.item] = brick

    def update_hud(self):
        score_text = f'SCORE: {self.score}'
        lives_text = f'LIVES: {self.lives}'
        
        if self.hud_score is None:
            self.hud_score = self.canvas.create_text(30, 25, text=score_text, font=('Segoe UI', 11, 'bold'), fill='#94a3b8', anchor='w')
            self.hud_lives = self.canvas.create_text(self.width - 30, 25, text=lives_text, font=('Segoe UI', 11, 'bold'), fill='#f43f5e', anchor='e')
        else:
            self.canvas.itemconfig(self.hud_score, text=score_text)
            self.canvas.itemconfig(self.hud_lives, text=lives_text)

    def start_game(self):
        self.canvas.unbind('<space>')
        self.canvas.delete(self.center_text)
        self.paddle.ball = None
        self.game_loop()

    def game_loop(self):
        self.paddle.update_position()
        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag('brick'))
        
        if num_bricks == 0:
            self.ball.speed = 0
            self.canvas.create_text(
                self.width / 2, self.height / 2,
                text='VICTORY!',
                font=('Segoe UI', 24, 'bold'),
                fill='#10b981'
            )
        elif self.ball.get_position()[3] >= self.height:
            self.ball.speed = 0
            self.lives -= 1
            self.update_hud()
            if self.lives < 0:
                self.canvas.create_text(
                    self.width / 2, self.height / 2,
                    text='GAME OVER',
                    font=('Segoe UI', 24, 'bold'),
                    fill='#f43f5e'
                )
            else:
                self.after(1000, self.setup_game)
        else:
            self.ball.update()
            # Jeda 12ms memberikan animasi tinggi (~80 FPS) yang sangat halus
            self.after(12, self.game_loop)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        
        for obj in objects:
            if isinstance(obj, Brick):
                self.score += 10
                self.update_hud()
                
        self.ball.collide(objects)


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Modern Fluid Brick Breaker')
    root.resizable(False, False)
    game = Game(root)
    game.mainloop()