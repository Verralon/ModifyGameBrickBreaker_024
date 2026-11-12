import tkinter as tk


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
        self.direction = [1, -1]
        self.speed = 7
        
        # Bola dengan efek bayangan/glow modern
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
        coords = self.get_position()
        width = self.canvas.winfo_width()
        
        # Pantulan dinding kiri/kanan
        if coords[0] <= 15 or coords[2] >= width - 15:
            self.direction[0] *= -1
        # Pantulan dinding atas (di bawah HUD)
        if coords[1] <= 60:
            self.direction[1] *= -1
            
        x = self.direction[0] * self.speed
        y = self.direction[1] * self.speed
        self.move(x, y)

    def collide(self, game_objects):
        coords = self.get_position()
        x = (coords[0] + coords[2]) * 0.5
        if len(game_objects) > 1:
            self.direction[1] *= -1
        elif len(game_objects) == 1:
            game_object = game_objects[0]
            coords = game_object.get_position()
            if x > coords[2]:
                self.direction[0] = 1
            elif x < coords[0]:
                self.direction[0] = -1
            else:
                self.direction[1] *= -1

        for game_object in game_objects:
            if isinstance(game_object, Brick):
                game_object.hit()


class Paddle(GameObject):
    def __init__(self, canvas, x, y):
        self.width = 100
        self.height = 12
        self.ball = None
        
        # Paddle dengan sudut melengkung modern (menggunakan polygon)
        item = canvas.create_rectangle(
            x - self.width / 2, y - self.height / 2,
            x + self.width / 2, y + self.height / 2,
            fill='#f43f5e', outline='', width=0
        )
        super(Paddle, self).__init__(canvas, item)

    def set_ball(self, ball):
        self.ball = ball

    def move(self, offset):
        coords = self.get_position()
        width = self.canvas.winfo_width()
        if coords[0] + offset >= 15 and coords[2] + offset <= width - 15:
            super(Paddle, self).move(offset, 0)
            if self.ball is not None:
                self.ball.move(offset, 0)


class Brick(GameObject):
    # Palet warna modern (Neon/Pastel dark mode)
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
        
        # Tema latar belakang gelap modern
        self.canvas = tk.Canvas(
            self, bg='#0f172a',
            width=self.width, height=self.height,
            highlightthickness=0
        )
        self.canvas.pack()
        self.pack()

        # Garis pembatas atas area bermain
        self.canvas.create_line(15, 50, self.width - 15, 50, fill='#334155', width=2)

        self.items = {}
        self.ball = None
        self.paddle = Paddle(self.canvas, self.width / 2, 420)
        self.items[self.paddle.item] = self.paddle
        
        # Spawn Bricks dengan jarak rapi
        for r, hits_val in enumerate([3, 2, 1]):
            for x in range(25, self.width - 25, 75):
                self.add_brick(x + 35, 90 + (r * 25), hits_val)

        self.hud_score = None
        self.hud_lives = None
        self.center_text = None
        
        self.setup_game()
        self.canvas.focus_set()
        
        # Kontrol Keyboard (Panah Kiri/Kanan & A/D)
        self.canvas.bind('<Left>', lambda _: self.paddle.move(-15))
        self.canvas.bind('<Right>', lambda _: self.paddle.move(15))
        self.canvas.bind('<a>', lambda _: self.paddle.move(-15))
        self.canvas.bind('<d>', lambda _: self.paddle.move(15))

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
        self.check_collisions()
        num_bricks = len(self.canvas.find_withtag('brick'))
        
        if num_bricks == 0:
            self.ball.speed = None
            self.canvas.create_text(
                self.width / 2, self.height / 2,
                text='VICTORY!',
                font=('Segoe UI', 24, 'bold'),
                fill='#10b981'
            )
        elif self.ball.get_position()[3] >= self.height:
            self.ball.speed = None
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
            # Sistem skor bertambah setiap balok hancur (opsional pelacak)
            self.after(20, self.game_loop)

    def check_collisions(self):
        ball_coords = self.ball.get_position()
        items = self.canvas.find_overlapping(*ball_coords)
        objects = [self.items[x] for x in items if x in self.items]
        
        # Tambah skor otomatis ketika bola mengenai brick
        for obj in objects:
            if isinstance(obj, Brick):
                self.score += 10
                self.update_hud()
                
        self.ball.collide(objects)


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Modern Brick Breaker')
    root.resizable(False, False)
    game = Game(root)
    game.mainloop()