import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, Gdk
import subprocess
import time
import logging

logging.basicConfig(
    filename="/home/lazybot/Desktop/bash/emoji_error.log",
    level=logging.ERROR,
    format="%(asctime)s - %(levelname)s - %(message)s"
)



class EmojiPopup(Gtk.Window):
    
    def __init__(self):
        super().__init__(title="Select an Emoji")
        self.set_border_width(10)

        css = b"""
        button:hover ,
        button:focus{
            background-color: #3a86ff;  /* bright yellow on hover */
            color: black;
            font-weight: bold;
        }
        """
        style_provider = Gtk.CssProvider()
        style_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            style_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )


        self.focus_out_timer_id = None
        self.connect("focus-in-event", self.on_focus_in)
        self.connect("focus-out-event", self.on_focus_out)
        self.connect("key-press-event", self.on_key_press)

        
        # Position window where the cursor is
        self.move_to_cursor()

        self.emoji_path = "/home/lazybot/Desktop/bash/emojis.txt"
        with open(self.emoji_path, "r", encoding="utf-8") as f:
        
            self.emojis = [line.strip() for line in f if line.strip()]


            box = Gtk.Box(spacing=10)
            self.add(box)

            grid = Gtk.Grid()
            grid.set_row_spacing(5)
            grid.set_column_spacing(5)

            first_button = None
            for index, emoji in enumerate(self.emojis):
                button = Gtk.Button(label=emoji)
                button.set_size_request(20, 20)
                button.get_child().set_markup(f"<span font='15'>{emoji}</span>")
                button.connect("clicked", self.on_emoji_clicked, emoji)

                button.connect("focus-in-event", self.on_button_focus, emoji)


                row = index // 5  # integer division to get the row
                col = index % 5   # modulus to get the column

                grid.attach(button, col, row, 1, 1)

                if index == 0:
                    first_button = button

            # Then add the grid to your container, e.g.:
            box.pack_start(grid, True, True, 0)

            # After adding to the UI:
            if first_button:
                first_button.grab_focus()

            self.connect("destroy", Gtk.main_quit)

    def on_emoji_clicked(self, widget, emoji, keyval=None):
        self.ignore_focus = True  # Temporarily ignore focus out
        logging.error(f" {keyval} is val.")

        # Determine how many times to type the emoji
        repeat = 1
        if keyval is not None:
            key_unicode = Gdk.keyval_name(keyval)
            if key_unicode and key_unicode.isdigit():
                repeat = int(key_unicode)

        try:
            with open(self.emoji_path, "r", encoding="utf-8") as f:
                emojis = [line.strip() for line in f if line.strip()]

            if emoji in emojis:
                emojis.remove(emoji)
            emojis.insert(0, emoji)

            with open(self.emoji_path, "w", encoding="utf-8") as f:
                for e in emojis:
                    f.write(e + "\n")
        except Exception as e:
            logging.error(f"Error updating emoji file: {e}")

        # Switch to previous window via Alt+Tab
        subprocess.run(["xdotool", "key", "alt+Tab"])
        time.sleep(0.2)

        # Send the emoji via unicode input, repeated as needed
        for _ in range(repeat):
            unicode_code = ''.join(f"{ord(c):x}" for c in emoji)
            subprocess.run(["xdotool", "key", "ctrl+shift+u"])
            subprocess.run(["xdotool", "type", unicode_code])
            subprocess.run(["xdotool", "key", "Return"])
            time.sleep(0.2)

        Gtk.main_quit()  # Exit entire app after 2 seconds
        

        # Move selected emoji to top in file


    def on_button_focus(self, widget, event, emoji):
        self.focused_emoji = emoji


    def on_focus_in(self, widget, event):
        self.ignore_focus = False

    def on_focus_out(self, widget, event): 
        if not self.ignore_focus:
            Gtk.main_quit()

    def on_key_press(self, widget, event):
        keyval = event.keyval

        if keyval == Gdk.KEY_Escape:
            self.hide()
            return True

        if Gdk.KEY_1 <= keyval <= Gdk.KEY_9:
            count = keyval - Gdk.KEY_0  # Or just int(Gdk.keyval_name(keyval))
            if hasattr(self, "focused_emoji"):
                emoji = self.focused_emoji
                self.on_emoji_clicked(None, emoji, keyval)
                return True

        return False


    def quit_after_timeout(self):           
            Gtk.main_quit()  # Exit entire app after 2 seconds
            return False  # Run once, remove timer automatically

    def move_to_cursor(self):
        display = Gdk.Display.get_default()
        seat = display.get_default_seat()
        pointer = seat.get_pointer()
        screen, cursor_x, cursor_y = pointer.get_position()

        offset_x, offset_y = 60, 60

        # Ensure widget is realized and size is known
        if not self.get_realized():
            self.realize()

        width, height = self.get_size()

        # Get monitor geometry
        monitor = display.get_monitor_at_point(cursor_x, cursor_y)
        monitor_geo = monitor.get_geometry()
        screen_x = monitor_geo.x
        screen_y = monitor_geo.y
        screen_width = monitor_geo.width
        screen_height = monitor_geo.height

        # Horizontal position: try left first
        left_x = cursor_x - width - offset_x
        right_x = cursor_x + offset_x

        if left_x >= screen_x:
            new_x = left_x
        else:
            # Not enough space on left, try right
            if right_x + width <= screen_x + screen_width:
                new_x = right_x
            else:
                # Clamp inside screen if both sides fail
                new_x = max(screen_x, min(left_x, screen_x + screen_width - width))

        # Vertical position: try above first
        above_y = cursor_y - height - offset_y
        below_y = cursor_y + offset_y

        if above_y >= screen_y:
            new_y = above_y
        else:
            if below_y + height <= screen_y + screen_height:
                new_y = below_y
            else:
                # Clamp vertically inside screen
                new_y = max(screen_y, min(above_y, screen_y + screen_height - height))

        self.move(new_x, new_y)



 

if __name__ == "__main__":
    win = EmojiPopup()
    win.show_all()
    Gtk.main()
