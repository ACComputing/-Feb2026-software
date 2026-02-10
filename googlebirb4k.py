import tkinter as tk

class PelicanBikeApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Pelican on a Bike")
        
        # Base dimensions for the coordinate system (the art is designed for 800x600)
        self.base_width = 800
        self.base_height = 600
        
        # Flat Design Palette (Twitter-ish / Twemoji style)
        self.colors = {
            "sky": "#55ACEE",      # Twitter Blue
            "road": "#66757F",     # Slate
            "stripe": "#CCD6DD",   # Light Gray
            "sun": "#FFCC4D",      # Sunny Yellow
            "cloud": "#FFFFFF",
            "pelican": "#F5F8FA",  # Almost White
            "wing": "#E1E8ED",     # Light Grey for contrast
            "beak": "#FFAC33",     # Orange
            "pouch": "#FFCC4D",    # Lighter Orange/Yellow
            "bike": "#DD2E44",     # Red
            "tire": "#292F33",     # Black/Dark Grey
            "rim": "#8899A6",      # Silver/Grey
            "leg": "#FFAC33",      # Orange legs
            "eye_bg": "#FFFFFF",
            "eye_pupil": "#292F33"
        }
        
        # Create canvas
        self.canvas = tk.Canvas(root, bg=self.colors["sky"], highlightthickness=0)
        self.canvas.pack(fill="both", expand=True)
        
        # Bind resize event to handle auto-scaling
        self.canvas.bind("<Configure>", self.on_resize)

    def on_resize(self, event):
        # Redraw content whenever the window size changes
        self.draw_scene(event.width, event.height)

    def draw_scene(self, width, height):
        self.canvas.delete("all")
        
        # Calculate scale to fit window while maintaining aspect ratio
        scale_x = width / self.base_width
        scale_y = height / self.base_height
        scale = min(scale_x, scale_y)
        
        # Calculate offsets to center the artwork
        content_w = self.base_width * scale
        content_h = self.base_height * scale
        offset_x = (width - content_w) / 2
        offset_y = (height - content_h) / 2
        
        # --- DRAWING PHASE ---
        # We draw everything using original 800x600 coordinates
        # and then scale/move the entire canvas content at the end.
        
        # 1. Background
        self.draw_scenery()
        
        # 2. Main Subjects
        # Center coordinates in base 800x600 system
        cx, cy = 250, 400 
        self.draw_bike(cx, cy)
        self.draw_pelican(cx, cy)
        
        # --- SCALING PHASE ---
        # Apply the calculated scale and centering offset to all elements
        self.canvas.scale("all", 0, 0, scale, scale)
        self.canvas.move("all", offset_x, offset_y)

    def draw_scenery(self):
        # Road (Flat slate color)
        self.canvas.create_rectangle(0, 480, 800, 600, fill=self.colors["road"], outline="")
        
        # Road stripes (Dashed, light gray)
        for i in range(0, 850, 120):
            self.canvas.create_rectangle(i, 530, i + 70, 540, fill=self.colors["stripe"], outline="")
        
        # Sun (No outline, just flat color)
        self.canvas.create_oval(650, 50, 750, 150, fill=self.colors["sun"], outline="")
        
        # Clouds (Fluffy, overlapping circles)
        self.draw_cloud(100, 100)
        self.draw_cloud(350, 60)
        self.draw_cloud(600, 120)

    def draw_cloud(self, x, y):
        c = self.colors["cloud"]
        # Multiple overlapping circles to create a "blob" cloud
        self.canvas.create_oval(x, y, x+50, y+50, fill=c, outline="")
        self.canvas.create_oval(x+25, y-15, x+75, y+35, fill=c, outline="")
        self.canvas.create_oval(x+50, y+5, x+100, y+55, fill=c, outline="")
        self.canvas.create_oval(x+20, y+20, x+80, y+55, fill=c, outline="")

    def draw_bike(self, x, y):
        # Constants
        wr = 60 # Wheel radius
        
        # Base Points
        bw_x, bw_y = x - 100, y + 100    # Back Wheel
        fw_x, fw_y = x + 150, y + 100    # Front Wheel
        crank_x, crank_y = x, y + 100    # Crank/Pedals
        seat_x, seat_y = x - 20, y       # Seat Post Top
        stem_x, stem_y = x + 120, y - 20 # Handlebar Stem
        
        # Wheels
        self.draw_wheel(bw_x, bw_y, wr)
        self.draw_wheel(fw_x, fw_y, wr)
        
        # Frame (Thick lines with rounded caps for a tube look)
        f_color = self.colors["bike"]
        width = 12
        
        # Rear Triangle & Seat Tube
        self.canvas.create_line(bw_x, bw_y, seat_x, seat_y + 10, width=width, fill=f_color, capstyle=tk.ROUND)
        self.canvas.create_line(bw_x, bw_y, crank_x, crank_y, width=width, fill=f_color, capstyle=tk.ROUND)
        self.canvas.create_line(crank_x, crank_y, seat_x, seat_y, width=width, fill=f_color, capstyle=tk.ROUND)
        
        # Main Body & Down Tube
        self.canvas.create_line(seat_x, seat_y + 20, stem_x, stem_y + 40, width=width, fill=f_color, capstyle=tk.ROUND)
        self.canvas.create_line(crank_x, crank_y, stem_x, stem_y + 40, width=width, fill=f_color, capstyle=tk.ROUND)
        
        # Fork & Handlebar Stem
        self.canvas.create_line(stem_x, stem_y, fw_x, fw_y, width=width, fill=self.colors["rim"], capstyle=tk.ROUND)
        self.canvas.create_line(stem_x, stem_y + 10, stem_x - 30, stem_y - 30, width=width, fill=self.colors["rim"], smooth=True, capstyle=tk.ROUND)
        
        # Handlebar Grip
        self.canvas.create_line(stem_x - 25, stem_y - 25, stem_x - 45, stem_y - 15, width=width, fill=self.colors["tire"], capstyle=tk.ROUND)
        
        # Seat (Simple Polygon)
        self.canvas.create_polygon(seat_x - 25, seat_y - 5, seat_x + 25, seat_y - 5, seat_x + 15, seat_y + 10, seat_x - 15, seat_y + 10, fill=self.colors["tire"], outline="")
        
        # Pedals
        self.canvas.create_oval(crank_x - 12, crank_y - 12, crank_x + 12, crank_y + 12, fill=self.colors["rim"], outline="")
        self.canvas.create_line(crank_x, crank_y, crank_x, crank_y + 35, width=8, fill=self.colors["rim"], capstyle=tk.ROUND)
        self.canvas.create_rectangle(crank_x - 15, crank_y + 35, crank_x + 15, crank_y + 50, fill=self.colors["tire"], outline="")

    def draw_wheel(self, x, y, r):
        # Tire (Thick outline)
        self.canvas.create_oval(x - r, y - r, x + r, y + r, fill="", outline=self.colors["tire"], width=15)
        # Rim (Thinner inner circle)
        self.canvas.create_oval(x - (r-10), y - (r-10), x + (r-10), y + (r-10), fill="", outline=self.colors["rim"], width=4)
        # Spokes (Minimalist cross)
        self.canvas.create_line(x - (r-10), y, x + (r-10), y, fill=self.colors["rim"], width=2)
        self.canvas.create_line(x, y - (r-10), x, y + (r-10), fill=self.colors["rim"], width=2)

    def draw_pelican(self, x, y):
        # Pelican base position relative to seat
        px, py = x - 20, y - 10
        
        p_color = self.colors["pelican"]
        w_color = self.colors["wing"]
        b_color = self.colors["beak"]
        pch_color = self.colors["pouch"]
        
        # Tail Feathers
        self.canvas.create_polygon(px - 40, py, px - 70, py - 15, px - 40, py - 30, fill=p_color, outline="")
        
        # Body (Round oval)
        self.canvas.create_oval(px - 45, py - 65, px + 45, py + 45, fill=p_color, outline="")
        
        # Wing (Smooth teardrop shape)
        self.canvas.create_polygon(px - 20, py - 30, px + 25, py - 10, px - 20, py + 20, fill=w_color, outline="", smooth=True)
        
        # Neck (Thick line with smooth curves)
        self.canvas.create_line(px + 35, py - 40, px + 55, py - 90, px + 45, py - 130, width=30, fill=p_color, capstyle=tk.ROUND, smooth=True)
        
        # Head
        hx, hy = px + 45, py - 135
        self.canvas.create_oval(hx - 25, hy - 25, hx + 25, hy + 25, fill=p_color, outline="")
        
        # Beak Top
        self.canvas.create_polygon(hx + 10, hy - 15, hx + 110, hy + 5, hx + 10, hy + 5, fill=b_color, outline="")
        
        # Beak Pouch (Saggy shape)
        self.canvas.create_polygon(
            hx + 10, hy, 
            hx + 60, hy + 55, 
            hx + 100, hy + 15, 
            hx + 105, hy + 5, 
            hx + 10, hy + 5, 
            fill=pch_color, outline="", smooth=True
        )
        
        # Eye (Cartoon style)
        self.canvas.create_oval(hx - 8, hy - 12, hx + 2, hy - 2, fill=self.colors["eye_bg"], outline="")
        self.canvas.create_oval(hx - 4, hy - 8, hx - 1, hy - 5, fill=self.colors["eye_pupil"], outline="")
        
        # Legs (Orange)
        leg_color = self.colors["leg"]
        hip_x, hip_y = px, py + 35
        knee_x, knee_y = px - 35, py + 75
        pedal_x, pedal_y = x, y + 135 # Adjusted for pedal position
        
        # Thigh (Baackward angled)
        self.canvas.create_line(hip_x, hip_y, knee_x, knee_y, width=10, fill=leg_color, capstyle=tk.ROUND)
        # Lower Leg (Forward angled)
        self.canvas.create_line(knee_x, knee_y, pedal_x, pedal_y, width=8, fill=leg_color, capstyle=tk.ROUND)
        # Webbed Foot
        self.canvas.create_polygon(pedal_x - 15, pedal_y, pedal_x + 15, pedal_y, pedal_x + 5, pedal_y - 10, fill=leg_color, outline="")

        # Arms/Wings (Reaching for handlebars)
        hand_x, hand_y = x + 85, y - 55
        self.canvas.create_line(px + 20, py - 40, hand_x, hand_y, width=10, fill=p_color, capstyle=tk.ROUND)

if __name__ == "__main__":
    root = tk.Tk()
    # Center window
    window_width = 800
    window_height = 600
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    position_top = int(screen_height / 2 - window_height / 2)
    position_right = int(screen_width / 2 - window_width / 2)
    root.geometry(f"{window_width}x{window_height}+{position_right}+{position_top}")
    
    app = PelicanBikeApp(root)
    root.mainloop()
