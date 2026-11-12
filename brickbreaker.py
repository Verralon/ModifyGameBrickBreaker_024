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
    def __init__(self, canvas, x, y, dx=5, dy=-5):
        self.radius = 8
        self.dx = dx
        self.dy = dy
        self.speed = 7
        self.active = True
        
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
        self.active = False

    def update(self):
        self.move(self.dx, self.speed * (self.dy / abs(self.dy) if self.dy != 0 else -1))
        coords = self.get_position()
        width = self.canvas.winfo_width()
        
        if coords[0] <= 15:
            self.dx = abs(self.dx)
        elif coords[2] >= width - 15:
            self.dx = -abs(self.dx)
            
        if coords[1] <= 60:
            self.dy = abs(self.dy)

    def set_vector(self, dx, dy):
        length = math.hypot(dx, dy)
        if length == 0:
            return
        self.dx = (dx / length) * self.speed
        self.dy = (dy / length) * self.speed


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 110
        self.height = 12
        self.balls = []
        self.velocity = 0
        self.max_speed = 12
        
        item = canvas.create_rectangle(
            x - self.width / 2, y - self.height / 2,
            x + self.width / 2, y + self.height / 2,
            fill='#f43f5e', outline='', width=0
        )
        super(Paddle, self).__init__(canvas, item)

    def update_position(self):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        
        if coords[0] + self.velocity >= 15 and coords[2] + self.velocity <= width - 15:
            super(Paddle, self).move(self.velocity, 0)
            for ball in self.balls:
                if ball and ball.get_position()[3] < self.get_position()[1]:
                    ball.move(self.velocity, 0)

    def move_to(self, new_x):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        current_center_x = (coords[0] + coords[2]) / 2
        offset = new_x - current_center_x
        
        if coords[0] + offset >= 15 and coords[2] + offset <= width - 15:
            super(Paddle, self).move(offset, 0)
            for ball in self.balls:
                if ball:
                    ball.move(offset, 0)


class Brick(GameObject):
    COLORS = {1: '#10b981', 2: '#f59e0b', 3: '#6366f1'}

    def __init__(self, canvas, x, y, hits, game_ref):
        self.width = 68
        self.height = 18
        self.hits = hits
        self.game_ref = game_ref
        color = Brick.COLORS[hits]
        
        self.item = canvas.create_rectangle(
            x - self.width / 2, y - self.height / 2,
            x + self.width / 2, y + self.height / 2,
            fill=color, outline='', tags='brick'
        )
        # Menampilkan teks angka sisa hit pada balok
        self.text_item = canvas.create_text(
            x, y, text=str(self.hits),
            font=('Segoe UI', 9, 'bold'), fill='#ffffff'
        )
        super(Brick, self).__init__(canvas, self.item)

    def get_position(self):
        return self.canvas.coords(self.item)

    def delete(self):
        self.canvas.delete(self.item)
        self.canvas.delete(self.text_item)

    def hit(self):
        self.hits -= 1
        if self.hits == 0:
            self.delete()
            self.game_ref.spawn_powerup(self.get_position())
        else:
            self.canvas.itemconfig(self.item, fill=Brick.COLORS[self.hits])
            self.canvas.itemconfig(self.text_item, text=str(self.hits))


class PowerUp(GameObject):
    def __init__(self, canvas, x, y, p_type):
        self.type = p_type  # 'double' atau 'clone'
        color = '#fbbf24' if p_type == 'double' else '#a855f7'
        label = '2X' if p_type == 'double' else 'MULTI'
        
        self.item = canvas.create_oval(x-12, y-12, x+12, y+12, fill=color, outline='')
        self.text = canvas.create_text(x, y, text=label, font=('Segoe UI', 7, 'bold'), fill='#ffffff')
        super(PowerUp, self).__init__(canvas, self.item)

    def get_position(self):
        return self.canvas.coords(self.item)

    def update(self):
        self.canvas.move(self.item, 0, 3)
        self.canvas.move(self.text, 0, 3)

    def delete(self):
        self.canvas.delete(self.item)
        self.canvas.delete(self.text)


class Game(tk.Frame):
    def __init__(self, master):
        super(Game, self).__init__(master)
        self.lives = 3
        self.score = 0
        self.score_multiplier = 1
        self.width = 650
        self.height = 480
        
        self.canvas = tk.Canvas(
            self, bg='#090d16',
            width=self.width, height=self.height,
            highlightthickness=0
        )
        self.canvas.pack()
        self.pack()

        # Background Bintang
        random.seed(42)
        for _ in range(40):
            bx = random.randint(20, self.width - 20)
            by = random.randint(60, self.height - 20)
            size = random.choice([1, 2])
            self.canvas.create_oval(bx, by, bx + size, by + size, fill='#1e293b', outline='')

        self.canvas.create_line(15, 50, self.width - 15, 50, fill='#1e293b', width=2)

        self.items = {}
        self.balls = []
        self.powerups = []
        self.paddle = Paddle(self.canvas, self.width / 2, 420)
        self.items[self.paddle.item] = self.paddle
        
        for r, hits_val in enumerate([3, 2, 1]):
            for x in range(25, self.width - 25, 75):
                self.add_brick(x + 35, 90 + (r * 25), hits_val)

        self.hud_score = None
        self.hud_lives = None
        self.hud_mult = None
        self.center_text = None
        self.is_running = False
        
        self.setup_game()
        self.canvas.focus_set()
        
        self.canvas.bind('<KeyPress-Left>', lambda _: self.start_move(-1))
        self.canvas.bind('<KeyRelease-Left>', lambda _: self.stop_move())
        self.canvas.bind('<KeyPress-Right>', lambda _: self.start_move(1))
        self.canvas.bind('<KeyRelease-Right>', lambda _: self.stop_move())
        self.canvas.bind('<KeyPress-a>', lambda _: self.start_move(-1))
        self.canvas.bind('<KeyRelease-a>', lambda _: self.stop_move())
        self.canvas.bind('<KeyPress-d>', lambda _: self.start_move(1))
        self.canvas.bind('<KeyRelease-d>', lambda _: self.stop_move())
        self.canvas.bind('<Motion>', lambda event: self.paddle.move_to(event.x))

    def start_move(self, direction):
        self.paddle.velocity = direction * self.paddle.max_speed

    def stop_move(self):
        self.paddle.velocity = 0

    def setup_game(self):
        for b in self.balls:
            b.delete()
        self.balls = []
        
        paddle_coords = self.paddle.get_position()
        x = (paddle_coords[0] + paddle_coords[2]) * 0.5
        new_ball = Ball(self.canvas, x, 405)
        self.balls.append(new_ball)
        self.paddle.balls = self.balls
        
        self.update_hud()
        self.center_text = self.canvas.create_text(
            self.width / 2, self.height / 2,
            text='PRESS SPACE TO START',
            font=('Segoe UI', 16, 'bold'),
            fill='#f8fafc'
        )
        self.canvas.bind('<space>', lambda _: self.start_game())

    def add_brick(self, x, y, hits):
        brick = Brick(self.canvas, x, y, hits, self)
        self.items[brick.item] = brick

    def spawn_powerup(self, brick_coords):
        if brick_coords and random.random() < 0.35:  # 35% peluang drop powerup
            x = (brick_coords[0] + brick_coords[2]) / 2
            y = (brick_coords[1] + brick_coords[3]) / 2
            p_type = random.choice(['double', 'clone'])
            pu = PowerUp(self.canvas, x, y, p_type)
            self.powerups.append(pu)

    def update_hud(self):
        score_text = f'SCORE: {self.score}'
        lives_text = f'LIVES: {self.lives}'
        mult_text = f'MULT: {self.score_multiplier}X' if self.score_multiplier > 1 else ''
        
        if self.hud_score is None:
            self.hud_score = self.canvas.create_text(30, 25, text=score_text, font=('Segoe UI', 11, 'bold'), fill='#94a3b8', anchor='w')
            self.hud_mult = self.canvas.create_text(150, 25, text=mult_text, font=('Segoe UI', 11, 'bold'), fill='#fbbf24', anchor='w')
            self.hud_lives = self.canvas.create_text(self.width - 30, 25, text=lives_text, font=('Segoe UI', 11, 'bold'), fill='#f43f5e', anchor='e')
        else:
            self.canvas.itemconfig(self.hud_score, text=score_text)
            self.canvas.itemconfig(self.hud_mult, text=mult_text)
            self.canvas.itemconfig(self.hud_lives, text=lives_text)

    def start_game(self):
        self.canvas.unbind('<space>')
        self.canvas.delete(self.center_text)
        self.paddle.balls = []
        if not self.is_running:
            self.is_running = True
            self.game_loop()

    def game_loop(self):
        self.paddle.update_position()
        
        # Update semua bola
        for ball in self.balls[:]:
            ball.update()
            self.check_collisions(ball)
            
            # Cek jika bola jatuh ke bawah
            if ball.get_position()[3] >= self.height:
                ball.delete()
                self.balls.remove(ball)

        # Update Power-ups
        paddle_coords = self.paddle.get_position()
        for pu in self.powerups[:]:
            pu.update()
            p_coords = pu.get_position()
            # Cek tabrakan powerup dengan paddle
            if (p_coords[2] >= paddle_coords[0] and p_coords[0] <= paddle_coords[2] and
                p_coords[3] >= paddle_coords[1] and p_coords[1] <= paddle_coords[3]):
                self.apply_powerup(pu.type)
                pu.delete()
                self.powerups.remove(pu)
            elif p_coords[1] >= self.height:
                pu.delete()
                self.powerups.remove(pu)

        num_bricks = len(self.canvas.find_withtag('brick'))
        
        if num_bricks == 0:
            self.is_running = False
            self.canvas.create_text(
                self.width / 2, self.height / 2,
                text='VICTORY!',
                font=('Segoe UI', 24, 'bold'),
                fill='#10b981'
            )
        elif len(self.balls) == 0:
            self.lives -= 1
            self.update_hud()
            if self.lives < 0:
                self.is_running = False
                self.canvas.create_text(
                    self.width / 2, self.height / 2,
                    text='GAME OVER',
                    font=('Segoe UI', 24, 'bold'),
                    fill='#f43f5e'
                )
            else:
                self.setup_game()
                self.is_running = False
        else:
            self.after(12, self.game_loop)

    def apply_powerup(self, p_type):
        if p_type == 'double':
            self.score_multiplier = 2
            self.update_hud()
        elif p_type == 'clone':
            # Clones/Multi-ball: Gandakan bola yang ada saat ini
            new_balls = []
            for ball in self.balls:
                coords = ball.get_position()
                x = (coords[0] + coords[2]) / 2
                y = (coords[1] + coords[3]) / 2
                b1 = Ball(self.canvas, x, y, dx=4, dy=-6)
                b2 = Ball(self.canvas, x, y, dx=-4, dy=-6)
                new_balls.extend([b1, b2])
            self.balls.extend(new_balls)

    def check_collisions(self, ball):
        ball_coords = ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        
        x = (ball_coords[0] + ball_coords[2]) * 0.5
        hit_brick = False
        
        for obj in objects:
            if isinstance(obj, Brick):
                obj.hit()
                self.score += 10 * self.score_multiplier
                self.update_hud()
                hit_brick = True

        if len(objects) > 1 or hit_brick:
            ball.dy *= -1
        elif len(objects) == 1:
            obj = objects[0]
            if isinstance(obj, Paddle):
                paddle_coords = obj.get_position()
                paddle_center = (paddle_coords[0] + paddle_coords[2]) / 2
                offset = x - paddle_center
                ball.set_vector(offset * 0.15, -abs(ball.dy))
            else:
                ball.dy *= -1


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Modern Brick Breaker with Power-Ups')
    root.resizable(False, False)
    game = Game(root)
    game.mainloop()