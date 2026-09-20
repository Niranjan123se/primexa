from django import forms

from ..models import VendorMachine, VendorShopPhoto


class VendorMachineForm(forms.ModelForm):
    """Vendor-editable machine inventory and matching specifications."""

    class Meta:
        model = VendorMachine
        fields = [
            "machine_name", "machine_type", "machine_quantity", "manufacturer",
            "model_number", "controller", "axis_count", "work_envelope",
            "x_travel_mm", "y_travel_mm", "z_travel_mm",
            "maximum_turning_diameter_mm", "maximum_turning_length_mm",
            "between_centers_distance_mm", "maximum_workpiece_weight_kg",
            "spindle_speed_rpm", "spindle_power_kw", "chuck_size_mm",
            "bar_capacity_mm", "maximum_load", "accuracy", "accuracy_microns",
            "is_active",
        ]
        labels = {
            "machine_quantity": "Number of identical machines",
            "axis_count": "Axis count",
            "x_travel_mm": "X travel (mm)", "y_travel_mm": "Y travel (mm)",
            "z_travel_mm": "Z travel (mm)",
            "maximum_turning_diameter_mm": "Maximum turning diameter (mm)",
            "maximum_turning_length_mm": "Maximum turning length (mm)",
            "between_centers_distance_mm": "Distance between centres (mm)",
            "maximum_workpiece_weight_kg": "Maximum workpiece weight (kg)",
            "spindle_speed_rpm": "Maximum spindle speed (RPM)",
            "spindle_power_kw": "Spindle power (kW)",
            "chuck_size_mm": "Chuck size (mm)", "bar_capacity_mm": "Bar capacity (mm)",
            "accuracy_microns": "Accuracy (microns)",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "form-check-input" if isinstance(field.widget, forms.CheckboxInput)
                else "form-control"
            )


class VendorPortfolioItemForm(forms.ModelForm):
    """A vendor-controlled public gallery item for shop and completed-work proof."""

    class Meta:
        model = VendorShopPhoto
        fields = ["image", "caption", "display_order", "is_public"]
        labels = {
            "image": "Shop, completed job, or proof image",
            "caption": "Project or proof description",
            "is_public": "Show this item on my public profile",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = (
                "form-check-input" if isinstance(field.widget, forms.CheckboxInput)
                else "form-control"
            )
