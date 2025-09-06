"""
Reflex Form Example with Validation and Submit Handling
"""

import reflex as rx
from typing import Dict, Any


class FormState(rx.State):
    """State for the form example."""
    
    # Form fields
    name: str = ""
    email: str = ""
    age: str = ""
    message: str = ""
    
    # Validation and feedback
    form_data: Dict[str, Any] = {}
    errors: Dict[str, str] = {}
    submitted: bool = False
    
    def validate_form(self) -> bool:
        """Validate form fields and return True if valid."""
        self.errors = {}
        
        # Name validation
        if not self.name.strip():
            self.errors["name"] = "Name is required"
        elif len(self.name.strip()) < 2:
            self.errors["name"] = "Name must be at least 2 characters"
            
        # Email validation
        if not self.email.strip():
            self.errors["email"] = "Email is required"
        elif "@" not in self.email or "." not in self.email:
            self.errors["email"] = "Please enter a valid email address"
            
        # Age validation
        if not self.age.strip():
            self.errors["age"] = "Age is required"
        else:
            try:
                age_int = int(self.age)
                if age_int < 1 or age_int > 120:
                    self.errors["age"] = "Age must be between 1 and 120"
            except ValueError:
                self.errors["age"] = "Age must be a number"
                
        # Message validation
        if not self.message.strip():
            self.errors["message"] = "Message is required"
        elif len(self.message.strip()) < 10:
            self.errors["message"] = "Message must be at least 10 characters"
            
        return len(self.errors) == 0
    
    def handle_submit(self, form_data: Dict[str, Any]):
        """Handle form submission with validation."""
        # Update state with form data
        self.name = form_data.get("name", "")
        self.email = form_data.get("email", "")
        self.age = form_data.get("age", "")
        self.message = form_data.get("message", "")
        
        # Validate the form
        if self.validate_form():
            # Form is valid - process the data
            self.form_data = {
                "name": self.name,
                "email": self.email,
                "age": int(self.age),
                "message": self.message,
                "submitted_at": "Just now"
            }
            self.submitted = True
            
            # Here you would typically save to database or send email
            print(f"Form submitted successfully: {self.form_data}")
        else:
            # Form has errors - they're already set in validate_form()
            self.submitted = False
    
    def reset_form(self):
        """Reset the form to initial state."""
        self.name = ""
        self.email = ""
        self.age = ""
        self.message = ""
        self.form_data = {}
        self.errors = {}
        self.submitted = False


def form_field(label: str, field_name: str, field_type: str = "text", 
               placeholder: str = "", required: bool = True):
    """Create a reusable form field component."""
    return rx.vstack(
        rx.hstack(
            rx.text(label, font_weight="bold"),
            rx.text("*", color="red") if required else rx.text(),
            spacing="0.1em"
        ),
        rx.cond(
            field_type == "textarea",
            rx.text_area(
                placeholder=placeholder,
                name=field_name,
                border_color=rx.cond(
                    FormState.errors[field_name],
                    "red",
                    "gray"
                ),
                border_width="2px",
                width="100%",
                height="100px"
            ),
            rx.input(
                placeholder=placeholder,
                name=field_name,
                type=field_type,
                border_color=rx.cond(
                    FormState.errors[field_name],
                    "red", 
                    "gray"
                ),
                border_width="2px",
                width="100%"
            )
        ),
        rx.cond(
            FormState.errors[field_name],
            rx.text(FormState.errors[field_name], color="red", font_size="sm"),
            rx.text("")
        ),
        width="100%",
        align_items="start",
        spacing="0.5em"
    )


def contact_form():
    """Create the main contact form component."""
    return rx.container(
        rx.heading("Contact Form", size="lg", margin_bottom="1em"),
        
        # Success message
        rx.cond(
            FormState.submitted,
            rx.alert(
                rx.alert_icon(),
                rx.alert_title("Form submitted successfully!"),
                rx.alert_description("Thank you for your message."),
                status="success",
                margin_bottom="1em"
            ),
            rx.text("")
        ),
        
        # The form
        rx.form(
            rx.vstack(
                form_field("Name", "name", placeholder="Enter your full name"),
                form_field("Email", "email", field_type="email", 
                          placeholder="Enter your email address"),
                form_field("Age", "age", field_type="number", 
                          placeholder="Enter your age"),
                form_field("Message", "message", field_type="textarea",
                          placeholder="Enter your message here..."),
                
                # Submit and reset buttons
                rx.hstack(
                    rx.button(
                        "Submit Form",
                        type="submit",
                        color_scheme="blue",
                        size="lg"
                    ),
                    rx.button(
                        "Reset Form",
                        type="button",
                        color_scheme="gray",
                        variant="outline",
                        size="lg",
                        on_click=FormState.reset_form
                    ),
                    spacing="1em",
                    width="100%",
                    justify="center"
                ),
                
                spacing="1em",
                width="100%"
            ),
            on_submit=FormState.handle_submit,
            reset_on_submit=False,  # We handle reset manually
            width="100%"
        ),
        
        # Display submitted data
        rx.cond(
            FormState.submitted,
            rx.vstack(
                rx.divider(margin_y="1em"),
                rx.heading("Submitted Data", size="md"),
                rx.code_block(
                    rx.foreach(
                        FormState.form_data,
                        lambda item: rx.text(f"{item[0]}: {item[1]}")
                    ),
                    language="json",
                    width="100%"
                ),
                width="100%"
            ),
            rx.text("")
        ),
        
        max_width="600px",
        padding="2em",
        margin_x="auto"
    )


def index():
    """Main page component."""
    return rx.vstack(
        contact_form(),
        width="100%",
        min_height="100vh",
        bg="gray.50",
        padding="2em"
    )


# Create the Reflex app
app = rx.App(
    theme=rx.theme(
        appearance="light",
        has_background=True,
        radius="medium",
        accent_color="blue",
    )
)
app.add_page(index, route="/")
