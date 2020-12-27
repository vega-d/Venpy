try:
    import gi
except Exception as e:
    if type(e) == ModuleNotFoundError:
        print('no GTK libraries were found!\n Attempting self install.')
        try:
            import os

            os.system('pip3 install pygobject elevate')
        except Exception as e:
            print('Failed self installtion. Trace:\n', e)
            exit(0)
        print('Successfully installed dependencies. Continuing.')
        import gi
    else:
        raise ModuleNotFoundError

# os.system("ls -l")
import os
import subprocess
import sys

# print(os.getcwd())

if os.geteuid() == 0:
    print("Running as root, continuing.")
else:
    print("Not launched as root, asking for root.\nThis is essential for app to work!")
    subprocess.call(['sudo', 'python3', *sys.argv])
    sys.exit()

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk


class Venpy(Gtk.Window):
    def __init__(self):
        Gtk.Window.__init__(self, title="Ventoy")
        self.terminal_command = None
        self.set_border_width(10)
        self.vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        self.disks_found = ['no disks detected']
        self.disks_combo = Gtk.ComboBoxText()
        self.disks_combo.set_entry_text_column(0)
        self.disks_combo.connect("changed", self.on_disk_chosen)
        self.disks_combo.set_active(1)
        self.vbox.pack_start(self.disks_combo, False, False, 0)

        self.refresh_button = Gtk.Button(label="refresh")
        self.refresh_button.connect("clicked", self.on_disks_update)
        self.vbox.pack_start(self.refresh_button, False, False, 0)

        self.hbox = Gtk.Box(spacing=6)

        button1 = Gtk.RadioButton.new_with_label_from_widget(None, "Install")
        button1.connect("toggled", self.on_mode_chosen, "1")
        self.hbox.pack_start(button1, False, False, 0)

        button2 = Gtk.RadioButton.new_from_widget(button1)
        button2.set_label("Force install")
        button2.connect("toggled", self.on_mode_chosen, "2")
        self.hbox.pack_start(button2, False, False, 0)

        button3 = Gtk.RadioButton.new_with_mnemonic_from_widget(button1, "Update")
        button3.connect("toggled", self.on_mode_chosen, "3")
        self.hbox.pack_start(button3, False, False, 0)

        self.vbox.pack_start(self.hbox, False, False, 0)
        self.hbox2 = Gtk.Box(spacing=6)

        self.secure_boot_checkbox = Gtk.CheckButton(label="Secure boot support")
        self.secure_boot_checkbox.connect("toggled", self.on_checked)
        self.hbox2.pack_start(self.secure_boot_checkbox, False, False, 0)

        self.GPT_partitioning_checkbox = Gtk.CheckButton(label="Use GPT partitioning")
        self.GPT_partitioning_checkbox.connect("toggled", self.on_checked)
        self.hbox2.pack_start(self.GPT_partitioning_checkbox, False, False, 0)

        text_expander = Gtk.Expander(label="Advanced Settings")
        text_expander.set_expanded(False)
        self.vbox.add(text_expander)
        text_expander.add(self.hbox2)

        self.start_button = Gtk.Button(label="Start")
        self.start_button.connect("clicked", self.flash)
        self.vbox.pack_start(self.start_button, False, False, 0)

        self.add(self.vbox)

        self.disk_selected = 'Select Disk'
        self.mode_selected = 'install'
        self.secure_boot_enabled = False
        self.GPT_partitioning_enabled = False
        self.advanced_settings_enabled = False

        # self.update_disk_combobox()
        self.on_disks_update()
        if not self.check_for_terminal():
            self.error_dialog(widget=self, text="No terminal found",
                              text_secondary="Please install a supported terminal app.\nApp will not work correctly.")

    def check_for_terminal(self):
        list_of_terminals = [
            ["gnome-terminal", ["gnome-terminal", "--"]],
            ["konsole", ["konsole", "-e"]],
            ["xfce4-terminal", ["xfce4-terminal", "-e"]],
            ["deepin-terminal", ["deepin-terminal", "-e"]]
        ]
        for term in list_of_terminals:
            supported = True
            try:
                f = open("/usr/bin/" + term[0])
            except Exception:
                supported = False

            finally:
                if supported:
                    f.close()
            print("checking for", term[0], 'and result for support is', supported)
            if supported:
                print('setting', term[0], "as terminal to use.")
                self.terminal_command = term[1]
                return True
        print('no supported terminals found')
        return False

    def error_dialog(self, widget, text, text_secondary):
        dialog = Gtk.MessageDialog(
            transient_for=self,
            flags=0,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.CANCEL,
            text=text,
        )
        dialog.format_secondary_text(
            text_secondary
        )
        dialog.run()
        # print("ERROR dialog closed")
        dialog.destroy()

    def update_disk_combobox(self):
        model = self.disks_combo.get_model()
        model.clear()
        if len(self.disks_found) > 0:
            for i in self.disks_found:
                self.disks_combo.append_text("%s - %s" % i)

    def on_disks_update(self, widget=None):
        import subprocess
        test1 = subprocess.Popen(["lsblk", "-o", "PATH"], stdout=subprocess.PIPE)
        test2 = subprocess.Popen(["lsblk", "-o", "TYPE"], stdout=subprocess.PIPE)
        test3 = subprocess.Popen(["lsblk", "-o", "SIZE"], stdout=subprocess.PIPE)

        disk_paths = test1.communicate()[0].decode("utf-8").split('\n')
        disk_types = test2.communicate()[0].decode("utf-8").split('\n')
        disk_sizes = test3.communicate()[0].decode("utf-8").split('\n')

        disks = []

        for i in range(len(disk_paths)):
            if disk_types[i] == 'disk':
                disks.append((disk_paths[i], disk_sizes[i]))

        self.disks_found = disks
        self.update_disk_combobox()

    def on_disk_chosen(self, combo):
        text = combo.get_active_text()
        if text is not None:
            self.disk_selected = text.split(' - ')[0]
            print("Selected disk:", self.disk_selected)
        else:
            print("no disk selected")

    def on_mode_chosen(self, button, name):
        if button.get_active():
            modes = ['install', 'finstall', 'rinstall']
            self.mode_selected = modes[int(name) - 1]
            print("Ventoy will", self.mode_selected)

    def on_checked(self, widget, data=None):
        self.secure_boot_enabled = self.secure_boot_checkbox.get_active()
        self.GPT_partitioning_enabled = self.GPT_partitioning_checkbox.get_active()

        print('secure boot support is', self.secure_boot_enabled, '; gpt partitioning is',
              self.GPT_partitioning_enabled, '; advanced settings are', self.advanced_settings_enabled)

    def flash(self, widget):
        cmd = self.terminal_command + ['sudo', "sh", "Ventoy2Disk.sh"]
        if self.mode_selected:
            if self.mode_selected == 'install':
                cmd.append('-i')
            if self.mode_selected == 'finstall':
                cmd.append('-I')
            if self.mode_selected == 'rinstall':
                cmd.append('-u')
            cmd.append(self.disk_selected)
            if self.GPT_partitioning_enabled:
                cmd.append('-g')
            if self.secure_boot_enabled:
                cmd.append('-s')
            # cmd += '&& read -n 1 -p Continue?'.split()
        else:
            pass
        print('executing', cmd)
        import subprocess
        flashing = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        # flashing.communicate('y')
        # output = flashing.communicate()[0].decode("utf-8").split('\n')
        # if len(output) > 7:
        #     output = output[7:]
        # for i in output:
        #     i = i.strip(r'\x1b[0m')
        #     i = i.strip(r'\x1b[31m')
        # print([output])


win = Venpy()
win.connect("destroy", Gtk.main_quit)
win.show_all()
Gtk.main()
