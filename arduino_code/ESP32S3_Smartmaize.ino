#include "WiFi.h"
#include "esp_camera.h"
#include "HTTPClient.h"
#include "WebServer.h"
#include "DHT.h"
#include <Wire.h>
#include <LiquidCrystal_I2C.h>

// WiFi credentials
const char* ssid = "Temiloluwa's Galaxy S10";
const char* password = "Temigoke253";

// Flask server endpoint
const char* serverName = "http://192.168.98.10:5000/upload";  // Update with your IP

// DHT11 sensor setup
#define DHTPIN 14      // Pin connected to the DHT11 sensor (change if necessary)
#define DHTTYPE DHT11  // Define the sensor type (DHT11)
DHT dht(DHTPIN, DHTTYPE); // Initialize DHT sensor

// ESP32 Camera pin configuration
#define CAMERA_MODEL_ESP32S3_EYE // Has PSRAM
#include "camera_pins.h"

// Web server for remote triggering
WebServer server(80);

// LED pin for flash (if available)
#define LED_PIN 4  // Adjust based on your board

// === Buzzer Setup ===
#define BUZZER_PIN 47   // connect buzzer to GPIO 15
void setup() {
  // Start Serial communication for debugging
  Serial.begin(115200);
  delay(1000);

  // Initialize LED pin
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);

  // Connect to Wi-Fi
  WiFi.begin(ssid, password);
  WiFi.setSleep(false);

  Serial.print("WiFi connecting");
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("");
  Serial.println("WiFi connected");
  Serial.print("ESP32 IP address: ");
  Serial.println(WiFi.localIP());

  // Initialize the camera
  if (!initCamera()) {
    Serial.println("Camera initialization failed!");
    return;
  }

  // Setting vertical flip
  sensor_t * s = esp_camera_sensor_get();
  if (s) {
    s->set_vflip(s, 1); // Set vertical flip
  }

  // Setup web server routes
  setupWebServer();

  Serial.println("=== ESP32 Camera Ready! ===");
  Serial.println("Commands:");
  Serial.println("1. Type 'capture' in Serial Monitor to take a photo");
  Serial.println("2. Visit http://" + WiFi.localIP().toString() + "/capture in browser");
  Serial.println("3. Use the web app's 'Take Photo' button");
  Serial.println("================================");
}

void loop() {
  // Handle web server requests
  server.handleClient();

  // Check for serial commands
  if (Serial.available()) {
    String command = Serial.readString();
    command.trim();
    
    if (command == "capture") {
      Serial.println("📸 Manual capture triggered from Serial Monitor!");
      captureAndUpload();
    }
  }

  delay(100); // Small delay to prevent excessive polling
}

void setupWebServer() {
  // Route to capture image
  server.on("/capture", HTTP_GET, []() {
    Serial.println("📸 Manual capture triggered from web request!");
    
    if (captureAndUpload()) {
      server.send(200, "application/json", 
        "{\"status\":\"success\",\"message\":\"Image captured and uploaded successfully!\"}");
    } else {
      server.send(500, "application/json", 
        "{\"status\":\"error\",\"message\":\"Failed to capture or upload image\"}");
    }
  });

  // Route to get camera status
  server.on("/status", HTTP_GET, []() {
    server.send(200, "application/json", 
      "{\"status\":\"online\",\"ip\":\"" + WiFi.localIP().toString() + "\",\"free_heap\":" + String(ESP.getFreeHeap()) + "}");
  });

  // Route for basic info page
  server.on("/", HTTP_GET, []() {
    String html = "<html><body>";
    html += "<h1>ESP32 Camera Controller</h1>";
    html += "<p>Camera Status: Online</p>";
    html += "<p>IP Address: " + WiFi.localIP().toString() + "</p>";
    html += "<button onclick='capturePhoto()' style='padding:10px 20px; font-size:16px;'>📸 Capture Photo</button>";
    html += "<div id='result'></div>";
    html += "<script>";
    html += "function capturePhoto() {";
    html += "  document.getElementById('result').innerHTML = 'Capturing...';";
    html += "  fetch('/capture').then(r => r.json()).then(data => {";
    html += "    document.getElementById('result').innerHTML = '<p>' + data.message + '</p>';";
    html += "  });";
    html += "}";
    html += "</script></body></html>";
    
    server.send(200, "text/html", html);
  });

  server.begin();
  Serial.println("Web server started on port 80");
}

bool captureAndUpload() {
  // Flash LED briefly to indicate capture
  digitalWrite(LED_PIN, HIGH);
  delay(100);
  digitalWrite(LED_PIN, LOW);

  Serial.println("=== Starting image capture ===");
  
  // Capture an image
  camera_fb_t *fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("❌ Camera capture failed - no image taken!");
    return false;
  }

  // Verify we actually have image data
  if (fb->len == 0) {
    Serial.println("❌ Camera returned empty image!");
    esp_camera_fb_return(fb);
    return false;
  }

  Serial.printf("✅ Image captured successfully!\n");
  Serial.printf("   - Size: %d bytes\n", fb->len);
  Serial.printf("   - Format: %s\n", (fb->format == PIXFORMAT_JPEG) ? "JPEG" : "Other");
  Serial.printf("   - Width: %d, Height: %d\n", fb->width, fb->height);

  // Check if image data looks valid (JPEG should start with 0xFF 0xD8)
  if (fb->len > 2 && fb->buf[0] == 0xFF && fb->buf[1] == 0xD8) {
    Serial.println("✅ Image data appears to be valid JPEG");
  } else {
    Serial.println("⚠️  Image data may not be valid JPEG format");
    Serial.printf("   - First bytes: 0x%02X 0x%02X\n", fb->buf[0], fb->buf[1]);
  }

  // Check WiFi connection
  if (WiFi.status() != WL_CONNECTED) {
    Serial.println("❌ WiFi not connected");
    esp_camera_fb_return(fb);
    return false;
  }

  Serial.println("📤 Uploading image to server...");
  
  // Send image to Flask server
  bool success = sendImageToServer(fb);
  
  if (success) {
    Serial.println("✅ Image uploaded and analyzed successfully!");
  } else {
    Serial.println("❌ Failed to upload image to server");
  }

  // Return the framebuffer to the camera driver
  esp_camera_fb_return(fb);

  return success;
}

bool sendImageToServer(camera_fb_t *fb) {
  HTTPClient http;
  
  // Begin HTTP connection
  if (!http.begin(serverName)) {
    Serial.println("HTTP begin failed");
    return false;
  }

  // Set headers
  http.addHeader("Content-Type", "application/octet-stream");
  http.addHeader("Content-Length", String(fb->len));
  http.addHeader("X-ESP32-Camera", "true"); // Custom header to identify ESP32

  // Send POST request with image data
  int httpResponseCode = http.POST(fb->buf, fb->len);
  
  // Check response
  if (httpResponseCode > 0) {
    String response = http.getString();
    Serial.printf("HTTP Response code: %d\n", httpResponseCode);
    Serial.printf("Response: %s\n", response.c_str());
    
    http.end(); // Clean up
    return (httpResponseCode == 200);
  } else {
    Serial.printf("HTTP POST failed, error: %s\n", http.errorToString(httpResponseCode).c_str());
    http.end(); // Clean up
    return false;
  }
}

bool initCamera() {
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.frame_size = FRAMESIZE_UXGA;
  config.pixel_format = PIXFORMAT_JPEG;
  config.grab_mode = CAMERA_GRAB_WHEN_EMPTY;
  config.fb_location = CAMERA_FB_IN_PSRAM;
  config.jpeg_quality = 12;
  config.fb_count = 1;

  // Optimize settings based on PSRAM availability
  if (config.pixel_format == PIXFORMAT_JPEG) {
    if (psramFound()) {
      config.jpeg_quality = 10;
      config.fb_count = 2;
      config.grab_mode = CAMERA_GRAB_LATEST;
    } else {
      // Limit the frame size when PSRAM is not available
      config.frame_size = FRAMESIZE_SVGA;
      config.fb_location = CAMERA_FB_IN_DRAM;
    }
  } else {
    // Best option for face detection/recognition
    config.frame_size = FRAMESIZE_240X240;
#if CONFIG_IDF_TARGET_ESP32S3
    config.fb_count = 2;
#endif
  }

  // Initialize the camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    return false;
  }
  
  Serial.println("Camera initialized successfully");
  return true;
}