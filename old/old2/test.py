import tkinter as tk
from tkinter import font
import random

class D20RollerApp:
    def __init__(self, root):
        self.root = root
        self.root.title("✨ The Crit-Finder 2000 ✨")
        self.root.geometry("400x450")
        self.root.configure(bg="#2b2b2b") # Dark grey background

        # --- Custom Fonts ---
        self.number_font = font.Font(family="Helvetica", size=120, weight="bold")
        self.label_font = font.Font(family="Helvetica", size=14)
        self.btn_font = font.Font(family="Helvetica", size=16, weight="bold")

        # --- GUI Elements ---
        
        # Title Label
        self.title_label = tk.Label(root, text="DND D20 ROLLER", 
                                    bg="#2b2b2b", fg="#aaaaaa", font=self.label_font)
        self.title_label.pack(pady=(30, 10))

        # The big number display area used for the roll result
        # We start with 'd20' displayed as a placeholder
        self.result_label = tk.Label(root, text="d20", 
                                     font=self.number_font, 
                                     bg="#2b2b2b", fg="#ffffff",
                                     width=4, height=1)
        self.result_label.pack(pady=20)

        # Status/Crit label underneath the number
        self.status_label = tk.Label(root, text="Ready to roll...", 
                                     bg="#2b2b2b", fg="#aaaaaa", font=self.label_font)
        self.status_label.pack(pady=10)

        # The Roll Button
        # We use relief="flat" and define colors for a modern look
        self.roll_button = tk.Button(root, text="🎲 ROLL THE DIE! 🎲", 
                                     command=self.start_roll_animation,
                                     font=self.btn_font, bg="#5cb85c", fg="white",
                                     activebackground="#4cae4c", activeforeground="white",
                                     relief="flat", padx=20, pady=10, cursor="hand2")
        self.roll_button.pack(side=tk.BOTTOM, pady=40)

        # Variables for animation state
        self.is_rolling = False
        self.animation_steps = 0

    def start_roll_animation(self):
        """Starts the rolling process."""
        if self.is_rolling:
            return

        self.is_rolling = True
        self.roll_button.config(state=tk.DISABLED, text="Rolling...", bg="#777777")
        self.status_label.config(text="Rolling...", fg="#aaaaaa")
        
        # Reset animation steps
        self.animation_steps = 25 # How many "flickers" before landing
        
        # Determine the final result NOW, but don't show it yet
        final_result = random.randint(1, 20)
        
        # Start the flickering effect loop
        self.animate_step(final_result)

    def animate_step(self, final_target):
        """
        Recursively calls itself using root.after() to update the display 
        rapidly, creating an animation effect.
        """
        if self.animation_steps > 0:
            # Show a random fake number while rolling
            fake_roll = random.randint(1, 20)
            self.result_label.config(text=str(fake_roll), fg="#aaaaaa")
            
            # Decrease steps remainin
            self.animation_steps -= 1
            # Schedule next update in 40ms (creates the fast flicker)
            self.root.after(40, lambda: self.animate_step(final_target))
        else:
            # Animation finished, land on the final number
            self.finalize_roll(final_target)

    def finalize_roll(self, result):
        """Displays the final result with fancy color formatting for crits."""
        self.result_label.config(text=str(result))
        
        if result == 20:
            # Natural 20 aesthetics
            self.result_label.config(fg="#FFD700") # Gold
            self.status_label.config(text="✨ CRITICAL HIT! Natural 20! ✨", fg="#FFD700")
            self.root.configure(bg="#1a3300") # Dark green background tint
            self.result_label.configure(bg="#1a3300")
        elif result == 1:
            # Natural 1 aesthetics
            self.result_label.config(fg="#ff3333") # Red
            self.status_label.config(text="☠️ CRITICAL MISS! Natural 1. ☠️", fg="#ff3333")
            self.root.configure(bg="#330a0a") # Dark red background tint
            self.result_label.configure(bg="#330a0a")
        else:
            # Standard roll aesthetics
            self.result_label.config(fg="#ffffff") # White
            self.status_label.config(text=f"Rolled a {result}", fg="#ffffff")
            self.root.configure(bg="#2b2b2b") # Reset background
            self.result_label.configure(bg="#2b2b2b")

        # Re-enable the button
        self.is_rolling = False
        self.roll_button.config(state=tk.NORMAL, text="🎲 ROLL AGAIN 🎲", bg="#5cb85c")

# --- Main Execution ---
if __name__ == "__main__":
    # Create the main window
    root = tk.Tk()
    # Initialize application
    app = D20RollerApp(root)
    # Start the main event loop to display the window
    root.mainloop()