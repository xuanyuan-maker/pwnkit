class HeapMenu:
    """Menu navigation helper for heap challenge templates."""

    def __init__(
        self,
        io,
        menu_prompt=None,
        add_opt=None,
        edit_opt=None,
        show_opt=None,
        delete_opt=None,
    ):
        self.io = io
        self.menu_prompt = menu_prompt
        self.add_opt = add_opt
        self.edit_opt = edit_opt
        self.show_opt = show_opt
        self.delete_opt = delete_opt

    def _select(self, option, name):
        if self.menu_prompt is None:
            raise ValueError("menu_prompt 未设置")
        if option is None:
            raise ValueError(f"{name}_opt 未设置")
        self.io.sendlineafter(self.menu_prompt, str(option).encode())

    def add(self):
        self._select(self.add_opt, "add")

    def edit(self):
        self._select(self.edit_opt, "edit")

    def show(self):
        self._select(self.show_opt, "show")

    def delete(self):
        self._select(self.delete_opt, "delete")
