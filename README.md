
# Smart Maize Disease Detection System

## Project Overview
This project is a final year Computer Engineering project that implements a smart system for detecting maize diseases using image classification and IoT-based environmental monitoring.

The system captures images of maize leaves using an ESP32-S3 camera module and collects temperature and humidity data using environmental sensors. The captured data is processed to identify possible disease conditions and provide feedback to the user.

## Objectives
- To design a smart system for maize disease detection
- To implement image-based disease classification
- To integrate IoT sensors for environmental monitoring
- To provide real-time feedback to farmers or users

## System Components
### Hardware
- ESP32-S3 with camera module
- DHT22 temperature and humidity sensor
- OLED display
- Power bank

### Software
- Arduino IDE
- Python
- VS Code

## ESP32-S3 Camera Pin Configuration

The table below shows the pin connections between the ESP32-S3 and the camera module used in this project.

// Camera pins for ESP32-S3 EYE camera module
#define CAMERA_MODEL_ESP32S3_EYE

#define PWDN_GPIO_NUM   -1  // No Power-down GPIO
#define RESET_GPIO_NUM  -1  // No Reset GPIO
#define XCLK_GPIO_NUM   15  // XCLK Pin
#define SIOD_GPIO_NUM   4   // SIOD Pin
#define SIOC_GPIO_NUM   5   // SIOC Pin

#define Y2_GPIO_NUM     11  // Y2 Pin
#define Y3_GPIO_NUM     9   // Y3 Pin
#define Y4_GPIO_NUM     8   // Y4 Pin
#define Y5_GPIO_NUM     10  // Y5 Pin
#define Y6_GPIO_NUM     12  // Y6 Pin
#define Y7_GPIO_NUM     18  // Y7 Pin
#define Y8_GPIO_NUM     17  // Y8 Pin
#define Y9_GPIO_NUM     16  // Y9 Pin

#define VSYNC_GPIO_NUM  6   // VSYNC Pin
#define HREF_GPIO_NUM   7   // HREF Pin
#define PCLK_GPIO_NUM   13  // PCLK Pin

## Model and Dataset Availability
Due to GitHub file size limitations, trained model files (.h5, .keras, etc.) and full datasets are not included.
Sample images are provided.
Full resources are available upon request.


## Project Structure
smart-maize-disease-detection/
arduino_code/ # ESP32-S3 firmware and sensor code
software/ # Image classification and application logic
images/ # Hardware setup, diagrams, and results
docs/ # Project report
README.md


## Author
**Temiloluwa Folorunso**  
Computer Engineering, Obafemi Awolowo University
