import hashlib
import json
import os
import random
import requests
from threading import Thread

from kivy.animation import Animation
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import NumericProperty, ObjectProperty, StringProperty, ListProperty
from kivy.uix.behaviors.button import ButtonBehavior
from kivy.uix.button import Button
from kivy.uix.dropdown import DropDown
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.utils import platform

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.card import MDCard
from kivymd.uix.card.card import MDSeparator
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.textfield import MDTextField
from kivy_garden.mapview.geojson import GeoJsonMapLayer

from plyer import accelerometer, camera
from utils import get_location
BASE_URL = "https://emergency-response-system-app.onrender.com"


# --- Custom Widgets ---
class ClickableMDLabel(ButtonBehavior, MDLabel):
    pass

class ClickableBoxLayout(ButtonBehavior, MDBoxLayout):
    pass

# --- Screen Classes ---
class SplashScreen(MDScreen):
    logo_y_offset = NumericProperty(0)

    def on_enter(self, *args):
        logo = self.ids.logo_image
        logo.opacity = 0
        fade_in_anim = Animation(opacity=1, duration=1.5, t='in_quad')
        fade_in_anim.start(logo)
        self.start_logo_gliding()
        Clock.schedule_once(self.start_exit_animation, 3.5)

    def start_logo_gliding(self):
        anim_up = Animation(logo_y_offset=0.05, duration=1, t='in_out_quad')
        anim_down = Animation(logo_y_offset=-0.05, duration=1, t='in_out_quad')
        anim_up.bind(on_complete=lambda *args: anim_down.start(self))
        anim_down.bind(on_complete=lambda *args: anim_up.start(self))
        anim_up.start(self)

    def start_exit_animation(self, dt):
        logo = self.ids.logo_image
        fade_out_anim = Animation(opacity=0, duration=1.0, t='out_quad')
        fade_out_anim.bind(on_complete=self.go_to_next_screen)
        fade_out_anim.start(logo)

    def go_to_next_screen(self, *args):
        Animation.cancel_all(self, 'logo_y_offset')
        Animation.cancel_all(self.ids.logo_image, 'opacity')
        self.manager.current = 'welcome_screen'

class WelcomeScreen(MDScreen):
    pass

class RegistrationScreen(MDScreen):
    def register(self):
        print("[REGISTRATION] Register button pressed.")
        mobile = self.ids.mobile_number_input.text
        kyc = self.ids.kyc_input.text
        emergency_contact = self.ids.emergency_contact_input.text

        if not mobile or not kyc or not emergency_contact:
            print("[REGISTRATION] Error: All fields are required.")
            return

        payload = {
            "mobile": mobile,
            "kyc": kyc,
            "emergency_contact": emergency_contact
        }

        try:
            response = requests.post(f"{BASE_URL}/register", json=payload)
            if response.status_code == 201:
                print(f"[REGISTRATION] User registered successfully: {response.json().get('user')}")
                self.manager.current = 'login_screen'
            else:
                print(f"[REGISTRATION] Error: {response.json().get('message')}")
        except requests.exceptions.RequestException as e:
            print(f"[REGISTRATION] Error: {e}")

class SideMenu(MDBoxLayout):
    pass

class HomeScreen(MDScreen):
    side_menu_open = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_alert_index = 0
        self.side_menu = SideMenu()
        self.add_widget(self.side_menu)
        self.side_menu.pos_hint = {'x': -1}
        self.alerts = []
        self.fall_detected = False
        self.freefall_start_time = None
        self.FREEFALL_THRESHOLD = 2.0 # m/s^2
        self.IMPACT_THRESHOLD = 20.0 # m/s^2
        self.FREEFALL_TIME = 0.2 # seconds

    def on_enter(self, *args):
        self.load_alerts()
        self.update_itinerary_panel()
        self.add_geofence_layer()
        Clock.schedule_interval(self.update_alert, 5)
        try:
            accelerometer.enable()
            Clock.schedule_interval(self.check_user_status, 1) # Check once a second
        except Exception as e:
            print(f"Failed to enable accelerometer: {e}")

    def add_geofence_layer(self):
        try:
            geojson_layer = GeoJsonMapLayer(source="website/northeast_india.geojson")
            self.ids.map_view.add_layer(geojson_layer)
        except Exception as e:
            print(f"Error adding geofence layer: {e}")

    def on_leave(self, *args):
        try:
            accelerometer.disable()
            Clock.unschedule(self.check_user_status)
        except Exception as e:
            print(f"Failed to disable accelerometer: {e}")

    def check_user_status(self, dt):
        self.check_acceleration(dt)
        self.check_geofence(dt)

    def check_geofence(self, dt):
        # Geofence for Northeast India and Uttarakhand (approximate)
        MIN_LAT, MAX_LAT = 21.5, 31.5
        MIN_LON, MAX_LON = 77.5, 97.5

        try:
            location = get_location()
            if location:
                lat, lon = location.latitude, location.longitude
                if not (MIN_LAT <= lat <= MAX_LAT and MIN_LON <= lon <= MAX_LON):
                    self.show_geofence_alert()
        except Exception as e:
            print(f"Error getting location for geofence: {e}")

    def show_geofence_alert(self):
        if not hasattr(self, 'geofence_dialog') or not self.geofence_dialog.is_open:
            self.geofence_dialog = MDDialog(
                title="High-Risk Zone",
                text="You are entering a high-risk zone.",
                buttons=[MDFlatButton(text="OK", on_release=lambda x: self.geofence_dialog.dismiss())],
            )
            self.geofence_dialog.open()

    def check_acceleration(self, dt):
        if self.fall_detected:
            return

        try:
            val = accelerometer.acceleration
            if not val or all(v is None for v in val):
                return

            magnitude = (val[0]**2 + val[1]**2 + val[2]**2)**0.5

            if magnitude < self.FREEFALL_THRESHOLD:
                if self.freefall_start_time is None:
                    self.freefall_start_time = Clock.get_time()
            else:
                if self.freefall_start_time is not None:
                    if (Clock.get_time() - self.freefall_start_time) > self.FREEFALL_TIME:
                        if magnitude > self.IMPACT_THRESHOLD:
                            print("FALL DETECTED!")
                            self.fall_detected = True
                            self.show_fall_dialog()
                    self.freefall_start_time = None
        except Exception as e:
            pass
    
    def show_fall_dialog(self):
        self.countdown_value = 60
        
        self.countdown_label = MDLabel(
            text=f"Sending SOS in {self.countdown_value} seconds...",
            halign="center",
            font_style="H6"
        )
        
        self.fall_dialog = MDDialog(
            title="Fall Detected!",
            type="custom",
            content_cls=self.countdown_label,
            buttons=[
                MDFlatButton(
                    text="I'M OK",
                    on_release=self.dismiss_fall_dialog
                ),
                MDFlatButton(
                    text="SOS",
                    on_release=self.trigger_sos_from_fall
                ),
            ],
        )
        self.fall_dialog.open()
        
        self.countdown_event = Clock.schedule_interval(self.update_countdown, 1)

    def update_countdown(self, dt):
        self.countdown_value -= 1
        self.countdown_label.text = f"Sending SOS in {self.countdown_value} seconds..."
        if self.countdown_value <= 0:
            self.trigger_sos_from_fall(self)

    def dismiss_fall_dialog(self, *args):
        Clock.unschedule(self.countdown_event)
        self.fall_dialog.dismiss()
        self.fall_detected = False

    def trigger_sos_from_fall(self, *args):
        Clock.unschedule(self.countdown_event)
        self.fall_dialog.dismiss()
        self.send_sos_notification()
        self.fall_detected = False

    def load_alerts(self):
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            alerts_path = os.path.join(script_dir, 'alerts.json')
            with open(alerts_path, 'r') as f:
                self.alerts = json.load(f)
                if not self.alerts:
                    self.alerts = ["No alerts available."]
        except (FileNotFoundError, json.JSONDecodeError):
            self.alerts = ["Could not load alerts."]

    def update_itinerary_panel(self):
        app = MDApp.get_running_app()
        user = app.current_user
        title_label = self.ids.itinerary_title_label
        summary_layout = self.ids.itinerary_summary_layout
        summary_layout.clear_widgets()

        if user and 'selected_itinerary' in user and user['selected_itinerary']:
            city_name = user['selected_itinerary']
            title_label.text = f"Trip Itinerary for {city_name}"
            
            try:
                script_dir = os.path.dirname(os.path.abspath(__file__))
                itineraries_path = os.path.join(script_dir, 'itineraries.json')
                with open(itineraries_path, 'r') as f:
                    itineraries = json.load(f)
                selected_itinerary = next((i for i in itineraries if i['city'] == city_name), None)

                if selected_itinerary:
                    for item in selected_itinerary['itinerary']:
                        day_label = MDLabel(
                            text=f"Day {item['day']}: {item['activity']}",
                            halign='left',
                            valign='middle',
                            size_hint_y=None
                        )
                        day_label.bind(texture_size=lambda instance, value: setattr(instance, 'height', value[1]))
                        day_label.bind(width=lambda instance, value: setattr(instance, 'text_size', (value, None)))
                        summary_layout.add_widget(day_label)
                else:
                    summary_layout.add_widget(MDLabel(text="Itinerary details not found.", halign='center'))
            except (FileNotFoundError, json.JSONDecodeError):
                summary_layout.add_widget(MDLabel(text="Could not load itinerary details.", halign='center'))
        else:
            title_label.text = "Select an Itinerary"

    def go_to_itinerary_list(self, *args):
        self.manager.current = 'itinerary_list_screen'

    def go_to_safety_score_screen(self, *args):
        self.manager.current = 'safety_score_screen'

    def update_alert(self, dt):
        if self.alerts:
            self.ids.alerts_label.text = self.alerts[self.current_alert_index]
            self.current_alert_index = (self.current_alert_index + 1) % len(self.alerts)

    def send_sos_notification(self):
        print("SOS signal sent from Home Screen! Notifying admin platform...")
        user = MDApp.get_running_app().current_user
        if not user:
            print("No user logged in.")
            return

        try:
            location = get_location()
            if location:
                lat = location.latitude
                lon = location.longitude
            else:
                print("Failed to get location, using random coordinates.")
                lat = random.uniform(9.0, 37.0)
                lon = random.uniform(68.0, 97.0)
        except Exception as e:
            print(f"Error getting location: {e}, using random coordinates.")
            lat = random.uniform(9.0, 37.0)
            lon = random.uniform(68.0, 97.0)

        payload = {
            "blockchainId": user.get("blockchain_id"),
            "phoneNumber": user.get("mobile"),
            "emergencyContact": user.get("emergency_contact"),
            "kycId": user.get("kyc"),
            "location": {
                "latitude": lat,
                "longitude": lon
            }
        }

        try:
            response = requests.post(f"{BASE_URL}/sos", json=payload)
            if response.status_code == 200:
                print(f"SOS signal sent successfully. Response: {response.text}")
            else:
                print(f"Failed to send SOS signal. Status code: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"Error sending SOS signal: {e}")

    def start_anomaly_report(self):
        if platform == 'android':
            from android.permissions import request_permission, Permission
            request_permission(Permission.CAMERA, self.camera_permission_callback)
        else:
            self.open_camera()

    def camera_permission_callback(self, permissions, grants):
        if all(grants):
            self.open_camera()
        else:
            print("Camera permission denied.")

    def open_camera(self):
        try:
            from datetime import datetime
            current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.photo_path = f"report_{current_time}.jpg"
            camera.take_picture(
                filename=self.photo_path,
                on_complete=self.anomaly_report_photo_callback
            )
        except Exception as e:
            print(f"Error opening camera: {e}")

    def anomaly_report_photo_callback(self, filepath):
        if filepath and os.path.exists(filepath):
            print(f"Photo saved at {filepath}")
            self.photo_path = filepath
            self.show_report_dialog()
        else:
            print("No photo taken or file not found.")

    def show_report_dialog(self):
        if not hasattr(self, 'dialog'):
            self.reason_input = MDTextField(
                hint_text="Reason for report",
                multiline=True,
            )
            self.dialog = MDDialog(
                title="Submit Anomaly Report",
                type="custom",
                content_cls=self.reason_input,
                buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        on_release=lambda x: self.dialog.dismiss()
                    ),
                    MDFlatButton(
                        text="SUBMIT",
                        on_release=self.submit_report
                    ),
                ],
            )
        self.dialog.open()

    def submit_report(self, *args):
        reason = self.reason_input.text
        photo_path = self.photo_path
        
        print(f"Submitting report with reason: {reason} and photo: {photo_path}")
        self.dialog.dismiss()

        app = MDApp.get_running_app()
        user_data = app.current_user
        
        try:
            location = get_location()
            if location:
                location_data = {"latitude": location.latitude, "longitude": location.longitude}
            else:
                location_data = {"latitude": "N/A", "longitude": "N/A"}
        except Exception as e:
            print(f"Could not get location for report: {e}")
            location_data = {"latitude": "Error", "longitude": "Error"}

        report_data = {
            'reason': reason,
            'user': json.dumps(user_data),
            'location': json.dumps(location_data)
        }
        
        try:
            with open(photo_path, 'rb') as f:
                files = {'image': (os.path.basename(photo_path), f, 'image/jpeg')}
                
                response = requests.post(
                    f"{BASE_URL}/report",
                    files=files,
                    data=report_data
                )
                
                if response.status_code == 200:
                    print("Report submitted successfully.")
                else:
                    print(f"Failed to submit report. Status: {response.status_code}, Response: {response.text}")

        except FileNotFoundError:
            print(f"Error: Could not find photo file at {photo_path}")
        except requests.exceptions.RequestException as e:
            print(f"Error submitting report: {e}")

    def toggle_side_menu(self):
        if self.side_menu_open:
            self.hide_side_menu()
        else:
            self.show_side_menu()

    def show_side_menu(self):
        anim = Animation(pos_hint={'x': 0}, duration=0.3)
        anim.start(self.side_menu)
        self.side_menu_open = True

    def hide_side_menu(self, *args):
        anim = Animation(pos_hint={'x': -1}, duration=0.3)
        anim.start(self.side_menu)
        self.side_menu_open = False

    def on_touch_down(self, touch):
        if self.side_menu_open and not self.side_menu.collide_point(*touch.pos):
            self.hide_side_menu()
            return True
        return super().on_touch_down(touch)

class ProfileScreen(MDScreen):
    def on_enter(self, *args):
        user = MDApp.get_running_app().current_user
        if user:
            self.ids.mobile_label.text = user.get('mobile', '')
            self.ids.kyc_label.text = user.get('kyc', '')
            self.ids.blockchain_id_label.text = user.get('blockchain_id', '')
            self.ids.profile_image.source = user.get('pfp', 'logo.png')

    def change_profile_picture(self):
        print("[PROFILE] Simulating changing profile picture...")

class MainAppScreen(MDScreen):
    def on_enter(self, *args):
        pass

class ItineraryListScreen(MDScreen):
    def on_enter(self):
        self.load_cities()

    def load_cities(self):
        city_list_layout = self.ids.city_list
        city_list_layout.clear_widgets()
        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            itineraries_path = os.path.join(script_dir, 'itineraries.json')
            with open(itineraries_path, 'r') as f:
                itineraries = json.load(f)
            for itinerary in itineraries:
                card = MDCard(
                    orientation='vertical',
                    size_hint_y=None,
                    height=dp(150),
                    size_hint_x=0.8,
                    pos_hint={'center_x': 0.5},
                    ripple_behavior=True,
                    on_release=lambda x, itinerary=itinerary: self.view_itinerary(itinerary)
                )
                image = Image(
                    source=f"{itinerary['city'].lower()}.jpg",
                    allow_stretch=True,
                    keep_ratio=False,
                    size_hint_y=0.7
                )
                label = MDLabel(
                    text=itinerary['city'],
                    halign='center',
                    size_hint_y=0.3
                )
                card.add_widget(image)
                card.add_widget(label)
                city_list_layout.add_widget(card)
        except (FileNotFoundError, json.JSONDecodeError):
            city_list_layout.add_widget(MDLabel(text="Could not load cities."))

    def view_itinerary(self, itinerary):
        MDApp.get_running_app().current_itinerary = itinerary
        self.manager.current = 'itinerary_detail_screen'

class ItineraryDetailScreen(MDScreen):
    def on_enter(self):
        self.populate_details()

    def populate_details(self):
        app = MDApp.get_running_app()
        itinerary = app.current_itinerary
        if not itinerary:
            return
        self.ids.city_name_label.text = f"Itinerary for {itinerary['city']}"
        details_layout = self.ids.itinerary_details_layout
        details_layout.clear_widgets()
        for item in itinerary['itinerary']:
            details_layout.add_widget(
                MDLabel(text=f"Day {item['day']}: {item['activity']}", size_hint_y=None, height=dp(40))
            )

    def select_itinerary(self):
        app = MDApp.get_running_app()
        user = app.current_user
        itinerary = app.current_itinerary
        if user and itinerary:
            app.current_user['selected_itinerary'] = itinerary['city']
            self.manager.current = 'home_screen'

class SafetyScoreScreen(MDScreen):
    def on_enter(self):
        if platform == 'android':
            from android.permissions import request_permissions, Permission
            request_permissions([Permission.ACCESS_FINE_LOCATION, Permission.ACCESS_COARSE_LOCATION], self.location_permission_callback)
        else:
            self.start_fetch_thread()

    def location_permission_callback(self, permissions, grants):
        if all(grants):
            self.start_fetch_thread()
        else:
            self.update_labels("Location permission denied.", "")

    def start_fetch_thread(self):
        self.ids.safety_score_display.text = "Fetching safety score..."
        self.ids.city_display.text = ""
        Thread(target=self.fetch_safety_score).start()

    def fetch_safety_score(self):
        try:
            location = get_location()
            if not location:
                self.update_labels("Could not get your location.", "")
                return
        except Exception as e:
            self.update_labels(f"Error getting location: {e}", "")
            return

        lat, lon = location.latitude, location.longitude

        try:
            headers = {'User-Agent': 'KivySafetyApp/1.0'}
            response = requests.get(
                f"https://nominatim.openstreetmap.org/reverse?format=json&lat={lat}&lon={lon}",
                headers=headers
            )
            response.raise_for_status()
            data = response.json()
            address = data.get('address', {})
            city = address.get('city') or address.get('town') or address.get('village')
            if not city:
                self.update_labels("Could not determine city from your location.", "")
                return
        except requests.exceptions.RequestException as e:
            self.update_labels(f"Error fetching city: {e}", "")
            return

        try:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            scores_path = os.path.join(script_dir, 'safety_scores.json')
            with open(scores_path, 'r') as f:
                safety_data = json.load(f)
            
            found_city_data = None
            for city_data in safety_data['cities']:
                if city_data['city'].lower() == city.lower():
                    found_city_data = city_data
                    break
            
            if found_city_data:
                score = found_city_data.get('score', 'N/A')
                status = found_city_data.get('status', 'Unknown')
                self.update_labels(f"{score}/5", f"({status}) for {city}")
            else:
                self.update_labels("N/A", f"No safety score data for {city}.")

        except Exception as e:
            self.update_labels(f"Error: {e}", "")

    def update_labels(self, score_text, city_text):
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self.set_label_texts(score_text, city_text))

    def set_label_texts(self, score_text, city_text):
        self.ids.safety_score_display.text = score_text
        self.ids.city_display.text = city_text

    def go_to_home_screen(self):
        self.manager.current = 'home_screen'

class LoginScreen(MDScreen):
    def login(self):
        mobile = self.ids.mobile_number_input.text
        if not mobile:
            print("Please enter a mobile number.")
            return

        payload = {"mobile": mobile}

        try:
            response = requests.post(f"{BASE_URL}/login", json=payload)
            if response.status_code == 200:
                user_found = response.json().get("user")
                print(f"Login successful for user with mobile: {mobile}")
                MDApp.get_running_app().current_user = user_found
                self.manager.current = 'home_screen'
            else:
                print("User not found. Please register.")
        except requests.exceptions.RequestException as e:
            print(f"Error during login: {e}")

class MyApp(MDApp):
    current_user = ObjectProperty(None)
    current_itinerary = ObjectProperty(None)

    def switch_theme(self):
        self.theme_cls.theme_style = 'Light' if self.theme_cls.theme_style == 'Dark' else 'Dark'

    def go_to_profile(self):
        self.root.current = 'profile_screen'
        if self.root.get_screen('home_screen').side_menu_open:
            self.root.get_screen('home_screen').toggle_side_menu()

    def logout(self):
        self.current_user = None
        self.root.current = 'login_screen'
        if self.root.get_screen('home_screen').side_menu_open:
            self.root.get_screen('home_screen').toggle_side_menu()

    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_palette = "Blue"
        sm = ScreenManager()
        Builder.load_file('splash.kv')
        Builder.load_file('welcome.kv')
        Builder.load_file('registration.kv')
        Builder.load_file('login.kv')
        Builder.load_file('profile.kv')
        Builder.load_file('sidemenu.kv')
        Builder.load_file('home.kv')
        Builder.load_file('main_app.kv')
        Builder.load_file('itinerary_list.kv')
        Builder.load_file('itinerary_detail.kv')
        Builder.load_file('safetyscore.kv')
        sm.add_widget(SplashScreen(name='splash_screen'))
        sm.add_widget(WelcomeScreen(name='welcome_screen'))
        sm.add_widget(RegistrationScreen(name='registration_screen'))
        sm.add_widget(LoginScreen(name='login_screen'))
        sm.add_widget(HomeScreen(name='home_screen'))
        sm.add_widget(ProfileScreen(name='profile_screen'))
        sm.add_widget(MainAppScreen(name='main_app_screen'))
        sm.add_widget(ItineraryListScreen(name='itinerary_list_screen'))
        sm.add_widget(ItineraryDetailScreen(name='itinerary_detail_screen'))
        sm.add_widget(SafetyScoreScreen(name='safety_score_screen'))
        return sm

if __name__ == '__main__':
    MyApp().run()
