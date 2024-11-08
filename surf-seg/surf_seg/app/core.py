
from trame.app import get_server
from trame.decorators import TrameApp, change, controller
from trame.ui.vuetify3 import SinglePageLayout
from trame.widgets import vuetify3, vtk, deckgl
from surf_seg.widgets import surf_seg as my_widgets
import pydeck as pdk
import pandas as pd


view_state = pdk.ViewState(latitude=37.7749295, longitude=-122.4194155, zoom=11, bearing=0, pitch=45)

defaultLayers = [
    "Bike Rentals",
    "Bart Stop Exits",
    "Bart Stop Names",
    "Outbound Flow",
]

# -----------------------------------------------------------------------------


def from_data_file(filename):
    url = (
        "https://raw.githubusercontent.com/streamlit/"
        "example-data/master/hello/v1/%s" % filename
    )
    return pd.read_json(url)


ALL_LAYERS = {
    "Bike Rentals": pdk.Layer(
        "HexagonLayer",
        data=from_data_file("bike_rental_stats.json"),
        get_position=["lon", "lat"],
        radius=200,
        elevation_scale=4,
        elevation_range=[0, 1000],
        extruded=True,
    ),
    "Bart Stop Exits": pdk.Layer(
        "ScatterplotLayer",
        data=from_data_file("bart_stop_stats.json"),
        get_position=["lon", "lat"],
        get_color=[200, 30, 0, 160],
        get_radius="[exits]",
        radius_scale=0.05,
    ),
    "Bart Stop Names": pdk.Layer(
        "TextLayer",
        data=from_data_file("bart_stop_stats.json"),
        get_position=["lon", "lat"],
        get_text="name",
        get_color=[0, 0, 0, 200],
        get_size=15,
        get_alignment_baseline="'bottom'",
    ),
    "Outbound Flow": pdk.Layer(
        "ArcLayer",
        data=from_data_file("bart_path_stats.json"),
        get_source_position=["lon", "lat"],
        get_target_position=["lon2", "lat2"],
        get_source_color=[200, 30, 0, 160],
        get_target_color=[200, 30, 0, 160],
        auto_highlight=True,
        width_scale=0.0001,
        get_width="outbound",
        width_min_pixels=3,
        width_max_pixels=30,
    ),
}

# ---------------------------------------------------------
# Engine class
# ---------------------------------------------------------

@TrameApp()
class MyTrameApp:
    def __init__(self, server=None):
        self.server = get_server(server, client_type="vue3")
        if self.server.hot_reload:
            self.server.controller.on_server_reload.add(self._build_ui)
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
            # with layout.toolbar:
            #     vuetify3.VSpacer()
            #     my_widgets.CustomWidget(
            #         attribute_name="Hello",
            #         py_attr_name="World",
            #         click=self.ctrl.widget_click,
            #         change=self.ctrl.widget_change,
            #     )
            #     vuetify3.VSpacer()
            #     vuetify3.VSlider(                    # Add slider
            #         v_model=("resolution", 6),      # bind variable with an initial value of 6
            #         min=3, max=60, step=1,          # slider range
            #         dense=True, hide_details=True,  # presentation setup
            #     )
            #     with vuetify3.VBtn(icon=True, click=self.ctrl.reset_camera):
            #         vuetify3.VIcon("mdi-crop-free")
            #     with vuetify3.VBtn(icon=True, click=self.reset_resolution):
            #         vuetify3.VIcon("mdi-undo")

            # Main content
            with layout.content:
                deckMap = deckgl.Deck(
                    mapbox_api_key="INSERT MAPBOX API KEY HERE",
                    style="width: 100vw;",
                    classes="fill-height",
                )
                self.ctrl.deck_update = deckMap.update
                vuetify3.VSelect(
                    style="position: absolute; top: 10px; left: 25px; width: 600px;",
                    items=("layerNames", defaultLayers),
                    v_model=("activeLayers", defaultLayers),
                    dense=True,
                    hide_details=True,
                    multiple=True,
                    chips=True,
                )
                # with vuetify3.VContainer(fluid=True, classes="pa-0 fill-height"):
                #     with vtk.VtkView() as vtk_view:                # vtk.js view for local rendering
                #         self.ctrl.reset_camera = vtk_view.reset_camera  # Bind method to controller
                #         with vtk.VtkGeometryRepresentation():      # Add representation to vtk.js view
                #             vtk.VtkAlgorithm(                      # Add ConeSource to representation
                #                 vtk_class="vtkConeSource",          # Set attribute value with no JS eval
                #                 state=("{ resolution }",)          # Set attribute value with JS eval
                #             )

            # Footer
            # layout.footer.hide()

            return layout
            
    
    @change("activeLayers")
    def update_map(self, activeLayers, **kwargs):
        selected_layers = [
            layer for layer_name, layer in ALL_LAYERS.items() if layer_name in activeLayers
        ]
        if selected_layers:
            deck = pdk.Deck(
                map_provider="mapbox",
                map_style="mapbox://styles/mapbox/light-v9",
                initial_view_state=view_state,
                layers=selected_layers
            )
            self.ctrl.deck_update(deck)
        else:
            self.state.error = "Layer update error"
