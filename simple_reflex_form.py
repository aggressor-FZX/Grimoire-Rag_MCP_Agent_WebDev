"""
Simple Reflex Form Example
"""

import reflex as rx


class SimpleFormState(rx.State):
    """Simple form state."""
    
    name: str = ""
    email: str = ""
    form_data: dict = {}
    submitted: bool = False
    
    def handle_submit(self, form_data: dict):
        """Handle form submission."""
        self.form_data = form_data
        self.submitted = True
        print(f"Form submitted: {form_data}")
    
    def reset_form(self):
        """Reset the form."""
        self.name = ""
        self.email = ""
        self.form_data = {}
        self.submitted = False


def simple_form():
    """Create a simple form."""
    return rx.container(
        rx.heading("Simple Contact Form"),
        
        rx.cond(
            SimpleFormState.submitted,
            rx.alert(
                rx.alert_title("Form submitted successfully!"),
                status="success"
            ),
            rx.text("")
        ),
        
        rx.form(
            rx.vstack(
                rx.input(
                    placeholder="Enter your name",
                    name="name",
                    required=True
                ),
                rx.input(
                    placeholder="Enter your email",
                    name="email",
                    type="email",
                    required=True
                ),
                rx.button("Submit", type="submit"),
                spacing="1em"
            ),
            on_submit=SimpleFormState.handle_submit,
            reset_on_submit=True,
        ),
        
        rx.cond(
            SimpleFormState.submitted,
            rx.vstack(
                rx.heading("Submitted Data:"),
                rx.text(f"Name: {SimpleFormState.form_data.get('name', '')}"),
                rx.text(f"Email: {SimpleFormState.form_data.get('email', '')}"),
            ),
            rx.text("")
        ),
        
        max_width="400px",
        margin="2em auto"
    )


def index():
    return simple_form()


app = rx.App()
app.add_page(index)
