# Thermal Camera HTTP Api

This is a brief description of the Http Api to access the camera resources.

## Configuration
- Port is set to 8088

- If you use the proxy first add `http://cloudwebsocket2-ir-cloud.espoo-apps.ilab.cloud/cameras/` and port is '80' (no need to specify port)
- If there is user and password:
    - user: admin
    - password: levitezer2018
    - To access from outside browser: http://user:password@cloudwebsocket2-ir-cloud.espoo-apps.ilab.cloud/cameras

##  Video streams

#### Original Thermal Image
the response is a 8-bit stream of jpeg images (motion jpeg) made from the thermal sensor readings.
```
GET /cam.mjpg
```

#### Thermal Image Mask
the response is a 8-bit stream of jpeg images (motion jpeg)
```
GET /mask.mjpg
```

#### Background Substraction
the response is a 8-bit stream of jpeg images (motion jpeg)
```
GET /background.mjpg
```

#### Heatmap
the response is a 8-bit stream of jpeg images (motion jpeg)
```
GET /heatmap.mjpg
```
#### Query parameters-
All parameters are optional

|   Name  | Type |                  Description                  |
|:-------:|:----:|:---------------------------------------------:|
| sizex   | int  | horizontal image size in pixels. default: 160 |
| sizey   | int  | vertical image size in pixels. default: 120   |
| quality | int  | jpeg quality from 1 to 100, default is 95     |

#### Example
```commandline
http://localhost:8088/cam.mjpg?sizex=400&sizey=300
```

## Data
### Telemetry (frame metadata)
Response is a JSON containing all telemetry of the last frame
```
GET /telemetry
```
#### Response Example
```json
{"raw_min_set": 3200, "right_temp": 2572, "sensor_version": 17, "raw_min": 2790, "left_temp": 2566, "time_counter": 54909, "fpa_temp": 30832, "frame_delay": 100, "bit_depth": 8, "frame_mean": 3439, "raw_max": 4035, "discard_packets": 54, "abs_sensor_temp": 3035, "raw_max_set": 5000, "center_temp": 2594, "frame_counter": 15409}
```

### Analysed data
```
GET /analysis
```
#### Response Example
```json
{"movement_detection": true, "people_count": 0, "fire_detection": false}
```

### color heatmap
Response is a png image
```
GET /colored_heatmap.png
```

## Logs
### Build logs
```commandline
GET /build.log
```
### Application logs
```commandline
GET /logs.log
```

## Commands
### Sync
```
PUT /sync
```

### Calibration
```
PUT /calibrate
```

### Delay
```
PUT /delay
```
#### Body
Delay between frames in milliseconds. Use it to set the framerate.
- `Content-Type` must be `text/plain`
- Accepts a number from 1 - 65025

### Set Minimum temperature
```
PUT /min
```
#### Body
Raw temperature
- `Content-Type` must be `text/plain`
- Accepts a number from 1 - 65025

### Set Max temperature
```
PUT /max
```
#### Body
Raw temperature
- `Content-Type` must be `text/plain`
- Accepts a number from 1 - 65025


### Automatic Maximum temperature
```
PUT /automax
```

### Automatic Minimum temperature
```
PUT /automin
```

### Reboot camera
```
PUT /reboot
```


### Update camera
```
PUT /update
```

#### Body
Version number
- `Content-Type` must be `text/plain`