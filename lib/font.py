class Font:
    def __init__(self, font_dict, width=8, height=8):
        self.font = font_dict
        self._height = height
        self._width = width
        
    def height(self):
        """Get the height of the font in pixels."""
        return self._height
        
    def max_width(self):
        """Get the maximum width of any character in the font."""
        return self._width
        
    def hmap(self):
        """Return True if the font is horizontally mapped, False otherwise."""
        return True
        
    def reverse(self):
        """Return True if the font bit order is reversed."""
        return False
        
    def get_ch(self, ch):
        """Get the bitmap for a character."""
        return self.font.get(ch, self.font.get('?', [0]*8))
        
    def get_width(self, _):
        """Get the width of a character."""
        return self._width
