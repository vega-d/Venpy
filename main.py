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

print(os.getcwd())

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
        self.set_border_width(10)
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)

        self.refresh_button = Gtk.Button(label="detect disks")
        self.refresh_button.connect("clicked", self.on_button_clicked)
        vbox.pack_start(self.refresh_button, False, False, 0)

        self.disks_found = ['no disks detected']

        self.disks_combo = Gtk.ComboBoxText()
        self.disks_combo.set_entry_text_column(0)
        self.disks_combo.connect("changed", self.on_disk_chosen)
        self.update_disk_combobox()

        self.disks_combo.set_active(0)
        vbox.pack_start(self.disks_combo, False, False, 0)

        hbox = Gtk.Box(spacing=6)

        button1 = Gtk.RadioButton.new_with_label_from_widget(None, "Install")
        button1.connect("toggled", self.on_mode_chosen, "1")
        hbox.pack_start(button1, False, False, 0)

        button2 = Gtk.RadioButton.new_from_widget(button1)
        button2.set_label("Force install")
        button2.connect("toggled", self.on_mode_chosen, "2")
        hbox.pack_start(button2, False, False, 0)

        button3 = Gtk.RadioButton.new_with_mnemonic_from_widget(button1, "Update")
        button3.connect("toggled", self.on_mode_chosen, "3")
        hbox.pack_start(button3, False, False, 0)

        vbox.pack_start(hbox, False, False, 0)
        hbox2 = Gtk.Box(spacing=6)

        self.secure_boot_checkbox = Gtk.CheckButton(label="Secure boot support")
        self.secure_boot_checkbox.connect("toggled", self.on_checked)
        hbox2.pack_start(self.secure_boot_checkbox, False, False, 0)
        self.GPT_partitioning_checkbox = Gtk.CheckButton(label="Use GPT partitioning")
        self.GPT_partitioning_checkbox.connect("toggled", self.on_checked)
        hbox2.pack_start(self.GPT_partitioning_checkbox, False, False, 0)

        vbox.pack_start(hbox2, False, False, 0)

        self.start_button = Gtk.Button(label="Start")
        self.start_button.connect("clicked", self.flash)
        vbox.pack_start(self.start_button, False, False, 0)

        self.add(vbox)

        self.disk_selected = ''
        self.mode_selected = 'install'
        self.secure_boot_enabled = False
        self.GPT_partitioning_enabled = False

    def update_disk_combobox(self):
        model = self.disks_combo.get_model()
        model.clear()
        if len(self.disks_found) > 1:
            for i in self.disks_found:
                self.disks_combo.append_text("%s - %s" % i)

    def on_button_clicked(self, widget):
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

    def on_mode_chosen(self, button, name):
        if button.get_active():
            modes = ['install', 'finstall', 'rinstall']
            self.mode_selected = modes[int(name) - 1]
            print("Ventoy will", self.mode_selected)

    def on_checked(self, widget, data=None):
        self.secure_boot_enabled = self.secure_boot_checkbox.get_active()
        self.GPT_partitioning_enabled = self.GPT_partitioning_checkbox.get_active()

        print('secure boot support is', self.secure_boot_enabled, 'and gpt partitioning is',
              self.GPT_partitioning_enabled)

    def flash(self, widget):
        cmd = ["gnome-terminal", '--wait', "--", 'sudo', "sh", "Ventoy2Disk.sh"]
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
