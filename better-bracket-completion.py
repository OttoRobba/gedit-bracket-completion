#        Gedit Better Bracket Completion plugin
#        Original Gemini plugin - Gary Haran
#        Copyright (C) 2005-2006 Gary Haran <gary.haran@gmail.com>
#
#        Gemini port to Gedit 3 - Shauna Gordon
#        Copyright (C) 2012 Shauna Gordon <shauna@shaunagordon.com>
#
#        Fixes and rebrand - Otto Robba
#        Copyright (C) 2017 Otto Robba <ottorobba@gmail.com>
#
#        This program is free software; you can redistribute it and/or modify
#        it under the terms of the GNU General Public License as published by
#        the Free Software Foundation; either version 2 of the License, or
#        (at your option) any later version.
#
#        This program is distributed in the hope that it will be useful,
#        but WITHOUT ANY WARRANTY; without even the implied warranty of
#        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
#        GNU General Public License for more details.
#
#        You should have received a copy of the GNU General Public License
#        along with this program; if not, write to the Free Software
#        Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA
#        02110-1301  USA

from gi.repository import Gtk, GObject, Gedit


class GeminiPlugin(GObject.Object, Gedit.WindowActivatable):
    window = GObject.property(type=Gedit.Window)

    start_keyvals = [34, 39, 96, 40, 91, 123]
    end_keyvals   = [34, 39, 96, 41, 93, 125]
    twin_start    = ['"',"'",'`','(','[','{']
    twin_end      = ['"',"'",'`',')',']','}']
    
    def __init__(self):
        GObject.Object.__init__(self)

    def do_activate(self):
        self._handler_id = self.window.connect('key-press-event', self.on_key_press)

    def do_deactivate(self):
        self.window.disconnect(self._handler_id)
    
    def on_key_press(self, view, event):
        buf = self.window.get_active_document()

        cursor_mark = buf.get_insert()
        cursor_iter = buf.get_iter_at_mark(cursor_mark)

        if event.keyval in self.start_keyvals or event.keyval in self.end_keyvals or event.keyval in (65288, 65293):
            back_iter = cursor_iter.copy()
            back_char = back_iter.backward_char()
            back_char = buf.get_text(back_iter, cursor_iter, True)

            forward_iter = cursor_iter.copy()
            forward_char = forward_iter.forward_char()
            forward_char = buf.get_text(cursor_iter, forward_iter, True)

            if event.keyval in self.start_keyvals:
                index = self.start_keyvals.index(event.keyval)
                start_str = self.twin_start[index]
                end_str = self.twin_end[index]
            else:
                index = -1
                start_str, end_str = None, None

            if event.keyval not in (65288, 65535) and index > -1:   
                # pad the selected text with twins
                start_iter = buf.get_iter_at_mark(buf.get_insert())
                end_iter = buf.get_iter_at_mark(buf.get_selection_bound())
                selected_text = start_iter.get_text(end_iter)

                buf.delete(start_iter, end_iter)
                buf.insert_at_cursor(start_str + selected_text + end_str)
                
                cursor_iter = buf.get_iter_at_mark(buf.get_insert())
                cursor_iter.backward_char()

                buf.place_cursor(cursor_iter)

                return True
            elif event.keyval == 65288 and back_char in self.twin_start and forward_char in self.twin_end:
                # delete twins when backspacing starting char next to ending char
                if self.twin_start.index(back_char) == self.twin_end.index(forward_char):
                    buf.delete(cursor_iter, forward_iter)
            elif event.keyval in self.end_keyvals:
                # stop people from closing an already closed pair
                index = self.end_keyvals.index(event.keyval)
                if self.twin_end[index] == forward_char :
                    buf.delete(cursor_iter, forward_iter)
            elif event.keyval == 65293 and forward_char == '}':
                # add proper indentation when hitting before a closing bracket
                cursor_iter = buf.get_iter_at_mark(buf.get_insert ())
                line_start_iter = cursor_iter.copy()
                view.backward_display_line_start(line_start_iter)

                line = buf.get_text(line_start_iter, cursor_iter, True)
                preceding_white_space_pattern = re.compile(r'^(\s*)')
                groups = preceding_white_space_pattern.search(line).groups()
                preceding_white_space = groups[0]
                plen = len(preceding_white_space)

                buf.insert_at_cursor('\n')
                buf.insert_at_cursor(preceding_white_space)
                buf.insert_at_cursor('\n')

                cursor_mark = buf.get_insert()
                cursor_iter = buf.get_iter_at_mark(cursor_mark)

                buf.insert_at_cursor(preceding_white_space)

                cursor_mark = buf.get_insert()
                cursor_iter = buf.get_iter_at_mark(cursor_mark)

                for i in range(plen + 1):
                    if cursor_iter.backward_char():
                        buf.place_cursor(cursor_iter)
                if view.get_insert_spaces_instead_of_tabs():
                    buf.insert_at_cursor(' ' * view.get_tab_width())
                else:
                    buf.insert_at_cursor('\t')
                return True
