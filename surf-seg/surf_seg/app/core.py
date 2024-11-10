
from trame.app import get_server
from trame.decorators import TrameApp, change, controller
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vuetify3, vtk, deckgl
from surf_seg.widgets import surf_seg as my_widgets
import pydeck as pdk
import pandas as pd
from .surf_seg import SurfSeg
import logging



# ---------------------------------------------------------
# Engine class
# ---------------------------------------------------------

@TrameApp()
class MyTrameApp:
    def __init__(self, server=None):
        self.server = get_server(server, client_type="vue3")
        if self.server.hot_reload:
            self.server.controller.on_server_reload.add(self._build_ui)
        logging.debug('surface segmentation')
        self.surf = SurfSeg('/home/jphardee/Desktop/Kitware/trame-surf-seg/surf-seg/tests/vertices.txt')
        logging.debug('build ui')
        self.ui = self._build_ui()

        # Set state variable
        self.state.trame__title = "surf-seg"
        self.state.resolution = 6

    @property
    def state(self):
        return self.server.state

    @property
    def ctrl(self):
        return self.server.controller


    @controller.set("reset_resolution")
    def reset_resolution(self):
        self.state.resolution = 6

    @change("resolution")
    def on_resolution_change(self, resolution, **kwargs):
        print(f">>> ENGINE(a): Slider updating resolution to {resolution}")

    @controller.set("widget_click")
    def widget_click(self):
        print(">>> ENGINE(a): Widget Click")

    @controller.set("widget_change")
    def widget_change(self):
        print(">>> ENGINE(a): Widget Change")

    def _build_ui(self, *args, **kwargs):
        with SinglePageLayout(self.server) as layout:
            # Toolbar
            layout.title.set_text("Trame / vtk.js")
            with layout.toolbar:
                vuetify3.VSpacer()
                my_widgets.CustomWidget(
                    attribute_name="Hello",
                    py_attr_name="World",
                    click=self.ctrl.widget_click,
                    change=self.ctrl.widget_change,
                )
                vuetify3.VSpacer()
                vuetify3.VSlider(                    # Add slider
                    v_model=("resolution", 6),      # bind variable with an initial value of 6
                    min=3, max=60, step=1,          # slider range
                    dense=True, hide_details=True,  # presentation setup
                )
                with vuetify3.VBtn(icon=True, click=self.ctrl.reset_camera):
                    vuetify3.VIcon("mdi-crop-free")
                with vuetify3.VBtn(icon=True, click=self.reset_resolution):
                    vuetify3.VIcon("mdi-undo")

            # Main content
            with layout.content:
                with vuetify3.VContainer(fluid=True, classes="pa-0 fill-height"):
                    view =  vtk.VtkRemoteView(
                        self.surf.surface_render_window, interactive_ratio=1
                    )           # vtk.js view for local rendering
                    self.ctrl.update_view = view.update
                    self.ctrl.reset_camera = view.reset_camera  # Bind method to controller


            # Footer
            layout.footer.hide()

            return layout
