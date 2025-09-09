import os
import asyncio
import base64
import json
import uuid
import sounddevice as sd
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext
import numpy as np
from PIL import Image, ImageTk, ImageDraw
from aws_sdk_bedrock_runtime.client import BedrockRuntimeClient, InvokeModelWithBidirectionalStreamOperationInput
from aws_sdk_bedrock_runtime.models import InvokeModelWithBidirectionalStreamInputChunk, BidirectionalInputPayloadPart
from aws_sdk_bedrock_runtime.config import Config, HTTPAuthSchemeResolver, SigV4AuthScheme
from smithy_aws_core.credentials_resolvers.environment import EnvironmentCredentialsResolver

# Audio configuration
INPUT_SAMPLE_RATE = 16000
OUTPUT_SAMPLE_RATE = 24000
CHANNELS = 1
CHUNK_SIZE = 1024
DTYPE = np.int16

class AvatarVisualizer:
    def __init__(self, master, width=300, height=400):
        self.master = master
        self.width = width
        self.height = height
        self.canvas = tk.Canvas(master, width=width, height=height, bg='black')
        self.canvas.pack()
        
        # Avatar states
        self.is_speaking = False
        self.is_listening = False
        self.current_emotion = "neutral"
        self.mouth_animation_frame = 0
        
        # Colors
        self.face_color = "#FFE0BD"
        self.eye_color = "#4169E1"
        self.mouth_color = "#FF6B6B"
        
        # Start animation loop
        self.animate()
    
    def set_speaking(self, speaking):
        self.is_speaking = speaking
        if not speaking:
            self.mouth_animation_frame = 0
    
    def set_listening(self, listening):
        self.is_listening = listening
    
    def set_emotion(self, emotion):
        self.current_emotion = emotion
    
    def draw_avatar(self):
        self.canvas.delete("all")
        
        # Head
        head_x = self.width // 2
        head_y = self.height // 2
        head_radius = 80
        
        # Face outline
        self.canvas.create_oval(
            head_x - head_radius, head_y - head_radius,
            head_x + head_radius, head_y + head_radius,
            fill=self.face_color, outline="black", width=2
        )
        
        # Eyes
        eye_y = head_y - 20
        left_eye_x = head_x - 25
        right_eye_x = head_x + 25
        eye_radius = 8
        
        # Eye animation based on listening state
        if self.is_listening:
            # Wider eyes when listening
            eye_radius = 12
            eye_color = "#32CD32"  # Green when listening
        else:
            eye_color = self.eye_color
        
        self.canvas.create_oval(
            left_eye_x - eye_radius, eye_y - eye_radius,
            left_eye_x + eye_radius, eye_y + eye_radius,
            fill=eye_color, outline="black"
        )
        self.canvas.create_oval(
            right_eye_x - eye_radius, eye_y - eye_radius,
            right_eye_x + eye_radius, eye_y + eye_radius,
            fill=eye_color, outline="black"
        )
        
        # Mouth animation
        mouth_x = head_x
        mouth_y = head_y + 20
        
        if self.is_speaking:
            # Animated mouth for speaking
            mouth_width = 30 + 10 * np.sin(self.mouth_animation_frame * 0.5)
            mouth_height = 15 + 5 * np.sin(self.mouth_animation_frame * 0.3)
            self.mouth_animation_frame += 1
        else:
            # Neutral mouth
            mouth_width = 20
            mouth_height = 8
        
        self.canvas.create_oval(
            mouth_x - mouth_width//2, mouth_y - mouth_height//2,
            mouth_x + mouth_width//2, mouth_y + mouth_height//2,
            fill=self.mouth_color, outline="black"
        )
        
        # Status indicator
        status_text = ""
        status_color = "white"
        if self.is_listening:
            status_text = "Listening..."
            status_color = "#32CD32"
        elif self.is_speaking:
            status_text = "Speaking..."
            status_color = "#FF6B6B"
        else:
            status_text = "Ready"
            status_color = "#87CEEB"
        
        self.canvas.create_text(
            self.width // 2, self.height - 30,
            text=status_text, fill=status_color, font=("Arial", 12, "bold")
        )
    
    def animate(self):
        self.draw_avatar()
        self.master.after(50, self.animate)  # 20 FPS

class VirtualAvatarPresenter:
    def __init__(self, model_id='amazon.nova-sonic-v1:0', region='us-east-1'):
        self.model_id = model_id
        self.region = region
        self.client = None
        self.stream = None
        self.response = None
        self.is_active = False
        self.prompt_name = str(uuid.uuid4())
        self.content_name = str(uuid.uuid4())
        self.audio_content_name = str(uuid.uuid4())
        self.audio_queue = asyncio.Queue()
        self.role = None
        self.display_assistant_text = False
        
        # Presentation topic
        self.presentation_topic = "Introduction to Artificial Intelligence"
        
        # GUI setup
        self.root = tk.Tk()
        self.root.title("Virtual Avatar Co-Presenter")
        self.root.geometry("800x600")
        self.root.configure(bg='#2E2E2E')
        
        self.setup_gui()
        
    def setup_gui(self):
        # Main frame
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Left panel - Avatar
        avatar_frame = ttk.LabelFrame(main_frame, text="Virtual Co-Presenter", padding=10)
        avatar_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 5))
        
        self.avatar = AvatarVisualizer(avatar_frame)
        
        # Right panel - Controls and transcript
        control_frame = ttk.LabelFrame(main_frame, text="Presentation Control", padding=10)
        control_frame.grid(row=0, column=1, sticky="nsew", padx=(5, 0))
        
        # Topic input
        ttk.Label(control_frame, text="Presentation Topic:").pack(anchor=tk.W)
        self.topic_var = tk.StringVar(value=self.presentation_topic)
        topic_entry = ttk.Entry(control_frame, textvariable=self.topic_var, width=50)
        topic_entry.pack(fill=tk.X, pady=(0, 10))
        
        # Control buttons
        button_frame = ttk.Frame(control_frame)
        button_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.start_btn = ttk.Button(button_frame, text="Start Presentation", 
                                   command=self.start_presentation)
        self.start_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.stop_btn = ttk.Button(button_frame, text="Stop", 
                                  command=self.stop_presentation, state=tk.DISABLED)
        self.stop_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        self.mute_btn = ttk.Button(button_frame, text="Mute/Unmute", 
                                  command=self.toggle_mute)
        self.mute_btn.pack(side=tk.LEFT)
        
        # Transcript area
        ttk.Label(control_frame, text="Conversation Transcript:").pack(anchor=tk.W, pady=(10, 0))
        self.transcript = scrolledtext.ScrolledText(control_frame, height=15, width=50)
        self.transcript.pack(fill=tk.BOTH, expand=True, pady=(5, 0))
        
        # Status bar
        self.status_var = tk.StringVar(value="Ready to start presentation")
        status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN)
        status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Configure grid weights
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(0, weight=1)
        
        # Audio state
        self.is_muted = False
        
    def _initialize_client(self):
        """Initialize the Bedrock client."""
        config = Config(
            endpoint_uri=f"https://bedrock-runtime.{self.region}.amazonaws.com",
            region=self.region,
            aws_credentials_identity_resolver=EnvironmentCredentialsResolver(),
            http_auth_scheme_resolver=HTTPAuthSchemeResolver(),
            http_auth_schemes={"aws.auth#sigv4": SigV4AuthScheme()}
        )
        self.client = BedrockRuntimeClient(config=config)
    
    async def send_event(self, event_json):
        """Send an event to the stream."""
        event = InvokeModelWithBidirectionalStreamInputChunk(
            value=BidirectionalInputPayloadPart(bytes_=event_json.encode('utf-8'))
        )
        await self.stream.input_stream.send(event)
    
    async def start_session(self):
        """Start a new session with Nova Sonic."""
        if not self.client:
            self._initialize_client()
            
        # Initialize the stream
        self.stream = await self.client.invoke_model_with_bidirectional_stream(
            InvokeModelWithBidirectionalStreamOperationInput(model_id=self.model_id)
        )
        self.is_active = True
        
        # Send session start event
        session_start = {
            "event": {
                "sessionStart": {
                    "inferenceConfiguration": {
                        "maxTokens": 1024,
                        "topP": 0.9,
                        "temperature": 0.7
                    }
                }
            }
        }
        await self.send_event(json.dumps(session_start))
        
        # Send prompt start event
        prompt_start = {
            "event": {
                "promptStart": {
                    "promptName": self.prompt_name,
                    "textOutputConfiguration": {
                        "mediaType": "text/plain"
                    },
                    "audioOutputConfiguration": {
                        "mediaType": "audio/lpcm",
                        "sampleRateHertz": 24000,
                        "sampleSizeBits": 16,
                        "channelCount": 1,
                        "voiceId": "matthew",
                        "encoding": "base64",
                        "audioType": "SPEECH"
                    }
                }
            }
        }
        await self.send_event(json.dumps(prompt_start))
        
        # Send system prompt for co-presentation
        text_content_start = {
            "event": {
                "contentStart": {
                    "promptName": self.prompt_name,
                    "contentName": self.content_name,
                    "type": "TEXT",
                    "interactive": True,
                    "role": "SYSTEM",
                    "textInputConfiguration": {
                        "mediaType": "text/plain"
                    }
                }
            }
        }
        await self.send_event(json.dumps(text_content_start))
        
        topic = self.topic_var.get()
        system_prompt = f"""You are a virtual co-presenter helping with a presentation on "{topic}". 
        You should:
        1. Complement what the human presenter says
        2. Add relevant insights and examples
        3. Ask clarifying questions to engage the audience
        4. Provide smooth transitions between topics
        5. Keep responses conversational and engaging, typically 1-3 sentences
        6. Act as a knowledgeable partner, not just a passive assistant
        
        The human will be speaking, and you should respond naturally as if you're both presenting to an audience together."""

        text_input = {
            "event": {
                "textInput": {
                    "promptName": self.prompt_name,
                    "contentName": self.content_name,
                    "content": system_prompt
                }
            }
        }
        await self.send_event(json.dumps(text_input))
        
        text_content_end = {
            "event": {
                "contentEnd": {
                    "promptName": self.prompt_name,
                    "contentName": self.content_name
                }
            }
        }
        await self.send_event(json.dumps(text_content_end))
        
        # Start processing responses
        self.response = asyncio.create_task(self._process_responses())
    
    async def start_audio_input(self):
        """Start audio input stream."""
        audio_content_start = {
            "event": {
                "contentStart": {
                    "promptName": self.prompt_name,
                    "contentName": self.audio_content_name,
                    "type": "AUDIO",
                    "interactive": True,
                    "role": "USER",
                    "audioInputConfiguration": {
                        "mediaType": "audio/lpcm",
                        "sampleRateHertz": 16000,
                        "sampleSizeBits": 16,
                        "channelCount": 1,
                        "audioType": "SPEECH",
                        "encoding": "base64"
                    }
                }
            }
        }
        await self.send_event(json.dumps(audio_content_start))
    
    async def send_audio_chunk(self, audio_bytes):
        """Send an audio chunk to the stream."""
        if not self.is_active or self.is_muted:
            return
            
        blob = base64.b64encode(audio_bytes)
        audio_event = {
            "event": {
                "audioInput": {
                    "promptName": self.prompt_name,
                    "contentName": self.audio_content_name,
                    "content": blob.decode('utf-8')
                }
            }
        }
        await self.send_event(json.dumps(audio_event))
    
    async def end_audio_input(self):
        """End audio input stream."""
        audio_content_end = {
            "event": {
                "contentEnd": {
                    "promptName": self.prompt_name,
                    "contentName": self.audio_content_name
                }
            }
        }
        await self.send_event(json.dumps(audio_content_end))
    
    async def end_session(self):
        """End the session."""
        if not self.is_active:
            return
            
        prompt_end = {
            "event": {
                "promptEnd": {
                    "promptName": self.prompt_name
                }
            }
        }
        await self.send_event(json.dumps(prompt_end))
        
        session_end = {
            "event": {
                "sessionEnd": {}
            }
        }
        await self.send_event(json.dumps(session_end))
        await self.stream.input_stream.close()
    
    def update_transcript(self, speaker, text):
        """Update the transcript in the GUI."""
        def update():
            self.transcript.insert(tk.END, f"{speaker}: {text}\n")
            self.transcript.see(tk.END)
        
        self.root.after(0, update)
    
    async def _process_responses(self):
        """Process responses from the stream."""
        try:
            while self.is_active:
                output = await self.stream.await_output()
                result = await output[1].receive()
                
                if result.value and result.value.bytes_:
                    response_data = result.value.bytes_.decode('utf-8')
                    json_data = json.loads(response_data)
                    
                    if 'event' in json_data:
                        # Handle content start event
                        if 'contentStart' in json_data['event']:
                            content_start = json_data['event']['contentStart'] 
                            self.role = content_start['role']
                            
                            # Update avatar state
                            if self.role == "ASSISTANT":
                                self.root.after(0, lambda: self.avatar.set_speaking(True))
                            elif self.role == "USER":
                                self.root.after(0, lambda: self.avatar.set_listening(True))
                            
                            # Check for speculative content
                            if 'additionalModelFields' in content_start:
                                additional_fields = json.loads(content_start['additionalModelFields'])
                                if additional_fields.get('generationStage') == 'SPECULATIVE':
                                    self.display_assistant_text = True
                                else:
                                    self.display_assistant_text = False
                        
                        # Handle content end event
                        elif 'contentEnd' in json_data['event']:
                            self.root.after(0, lambda: self.avatar.set_speaking(False))
                            self.root.after(0, lambda: self.avatar.set_listening(False))
                                
                        # Handle text output event
                        elif 'textOutput' in json_data['event']:
                            text = json_data['event']['textOutput']['content']    
                           
                            if (self.role == "ASSISTANT" and self.display_assistant_text):
                                self.update_transcript("Avatar", text)
                            elif self.role == "USER":
                                self.update_transcript("You", text)
                        
                        # Handle audio output
                        elif 'audioOutput' in json_data['event']:
                            audio_content = json_data['event']['audioOutput']['content']
                            audio_bytes = base64.b64decode(audio_content)
                            await self.audio_queue.put(audio_bytes)
        except Exception as e:
            print(f"Error processing responses: {e}")
    
    async def play_audio(self):
        """Play audio responses using sounddevice."""
        try:
            with sd.OutputStream(
                samplerate=OUTPUT_SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocksize=CHUNK_SIZE
            ) as stream:
                while self.is_active:
                    audio_data = await self.audio_queue.get()
                    if not self.is_muted:
                        # Convert bytes to numpy array
                        audio_array = np.frombuffer(audio_data, dtype=DTYPE)
                        # Reshape for sounddevice (frames, channels)
                        audio_array = audio_array.reshape(-1, CHANNELS)
                        stream.write(audio_array)
        except Exception as e:
            print(f"Error playing audio: {e}")

    async def capture_audio(self):
        """Capture audio from microphone and send to Nova Sonic."""
        await self.start_audio_input()
        
        try:
            with sd.InputStream(
                samplerate=INPUT_SAMPLE_RATE,
                channels=CHANNELS,
                dtype=DTYPE,
                blocksize=CHUNK_SIZE
            ) as stream:
                while self.is_active:
                    audio_data, overflowed = stream.read(CHUNK_SIZE)
                    if not overflowed:
                        # Convert numpy array to bytes
                        audio_bytes = audio_data.astype(DTYPE).tobytes()
                        await self.send_audio_chunk(audio_bytes)
                    await asyncio.sleep(0.01)
        except Exception as e:
            print(f"Error capturing audio: {e}")
        finally:
            await self.end_audio_input()
    
    def start_presentation(self):
        """Start the presentation session."""
        self.presentation_topic = self.topic_var.get()
        self.start_btn.config(state=tk.DISABLED)
        self.stop_btn.config(state=tk.NORMAL)
        self.status_var.set("Starting presentation...")
        
        # Start the async session in a separate thread
        def run_session():
            # Create a new event loop for this thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Create a new audio queue for this event loop
            self.audio_queue = asyncio.Queue()
            
            async def session():
                await self.start_session()
                
                # Start audio tasks
                playback_task = asyncio.create_task(self.play_audio())
                capture_task = asyncio.create_task(self.capture_audio())
                
                # Update status
                self.root.after(0, lambda: self.status_var.set("Presentation active - Speak to co-present!"))
                
                # Wait for session to end
                while self.is_active:
                    await asyncio.sleep(0.1)
                
                # Clean up
                for task in [playback_task, capture_task]:
                    if not task.done():
                        task.cancel()
                await asyncio.gather(playback_task, capture_task, return_exceptions=True)
                
                await self.end_session()
                
                if self.response and not self.response.done():
                    self.response.cancel()
            
            try:
                loop.run_until_complete(session())
            except Exception as e:
                print(f"Session error: {e}")
            finally:
                loop.close()
        
        thread = threading.Thread(target=run_session)
        thread.daemon = True
        thread.start()
    
    def stop_presentation(self):
        """Stop the presentation session."""
        self.is_active = False
        self.start_btn.config(state=tk.NORMAL)
        self.stop_btn.config(state=tk.DISABLED)
        self.status_var.set("Presentation stopped")
        self.avatar.set_speaking(False)
        self.avatar.set_listening(False)
    
    def toggle_mute(self):
        """Toggle mute state."""
        self.is_muted = not self.is_muted
        status = "muted" if self.is_muted else "unmuted"
        self.status_var.set(f"Audio {status}")
    
    def run(self):
        """Run the GUI application."""
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.root.mainloop()
    
    def on_closing(self):
        """Handle window closing."""
        if self.is_active:
            self.stop_presentation()
        self.root.destroy()

def main():
    # Create the virtual avatar presenter
    presenter = VirtualAvatarPresenter()
    
    # Add instructions to the transcript
    presenter.transcript.insert(tk.END, "=== Virtual Avatar Co-Presenter ===\n")
    presenter.transcript.insert(tk.END, "Instructions:\n")
    presenter.transcript.insert(tk.END, "1. Enter your presentation topic above\n")
    presenter.transcript.insert(tk.END, "2. Click 'Start Presentation'\n")
    presenter.transcript.insert(tk.END, "3. Begin speaking about your topic\n")
    presenter.transcript.insert(tk.END, "4. The avatar will respond and co-present with you\n")
    presenter.transcript.insert(tk.END, "5. Use 'Mute/Unmute' to control audio\n")
    presenter.transcript.insert(tk.END, "6. Click 'Stop' when finished\n\n")
    
    # Run the application
    presenter.run()

if __name__ == "__main__":
    # Set AWS credentials directly (replace with your actual credentials)
    os.environ['AWS_ACCESS_KEY_ID'] = "TBD"
    os.environ['AWS_SECRET_ACCESS_KEY'] = "TBD"
    os.environ['AWS_DEFAULT_REGION'] = "us-east-1"
    
    # Verify credentials are set
    if not all(key in os.environ for key in ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']):
        print("❌ AWS credentials not properly set!")
        print("Please update the credentials in the code:")
        print("os.environ['AWS_ACCESS_KEY_ID'] = 'your-actual-access-key'")
        print("os.environ['AWS_SECRET_ACCESS_KEY'] = 'your-actual-secret-key'")
    else:
        print("✅ AWS credentials loaded")
        main()