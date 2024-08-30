from flask import Flask, render_template, request, redirect, url_for, send_file
from PIL import Image
import os
import csv

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/images/'
app.secret_key = 'supersecretkey'

points = [
    "rightcorner-upper", "rightcorner-bottom", "rightarea-upper-right", 
    "rightarea-upper-left", "rightarea-bottom-right", "rightarea-bottom-left", 
    "rightgoal-upper", "rightgoal-bottom", "center-spot", "leftcorner-upper", 
    "leftcorner-bottom", "leftarea-upper-right", "leftarea-upper-left", 
    "leftarea-bottom-right", "leftarea-bottom-left", "leftgoal-upper", 
    "leftgoal-bottom"
]
current_point = 0
coords = [None] * len(points)

@app.route('/', methods=['GET', 'POST'])
def index():
    global current_point
    error = None
    if request.method == 'POST':
        if 'image' not in request.files:
            error = "No file part"
        file = request.files['image']
        if file.filename == '':
            error = "No selected file"
        if file:
            try:
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], 'uploaded_image.png')
                file.save(file_path)
                
                # Resize the uploaded image
                uploaded_image = Image.open(file_path)
                uploaded_image.thumbnail((uploaded_image.width // 2, uploaded_image.height // 2), Image.LANCZOS)
                uploaded_image.save(file_path)

                current_point = 0
                return redirect(url_for('click_image'))
            except Exception as e:
                error = f"Error processing the image: {str(e)}"

    return render_template('index.html', error=error)

@app.route('/click_image', methods=['GET', 'POST'])
def click_image():
    global current_point, coords
    if request.method == 'POST':
        if current_point >= len(points):
            return redirect(url_for('save_coordinates'))
        
        x = request.form.get('x')
        y = request.form.get('y')
        skip = request.form.get('skip')
        if skip == "0":  # Not skipping
            coords[current_point] = (x, y)
        current_point += 1

        if current_point >= len(points):
            return redirect(url_for('save_coordinates'))

        point_name = points[current_point]
        prompt_image_path = os.path.join('static/images', f"{point_name}.png")

        # Resize the prompt image to one-third the size of the loaded image
        uploaded_image = Image.open(os.path.join(app.config['UPLOAD_FOLDER'], 'uploaded_image.png'))
        prompt_image = Image.open(prompt_image_path)
        new_size = (uploaded_image.width // 3, uploaded_image.height // 3)
        prompt_image = prompt_image.resize(new_size, Image.LANCZOS)
        prompt_image.save(prompt_image_path)

        return render_template('click_image.html', point_name=point_name, prompt_image_path=prompt_image_path)

    if current_point >= len(points):
        return redirect(url_for('save_coordinates'))

    point_name = points[current_point]
    prompt_image_path = os.path.join('static/images', f"{point_name}.png")

    return render_template('click_image.html', point_name=point_name, prompt_image_path=prompt_image_path)

@app.route('/save_coordinates')
def save_coordinates():
    global coords, points
    csv_file_path = 'coordinates.csv'
    with open(csv_file_path, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Point", "X", "Y"])
        for point_name, coord in zip(points, coords):
            if coord is not None:
                writer.writerow([point_name, coord[0], coord[1]])
            else:
                writer.writerow([point_name, "", ""])

    # Return the template and the file download separately
    return render_template('complete.html')

@app.route('/download_csv')
def download_csv():
    csv_file_path = 'coordinates.csv'
    return send_file(csv_file_path, as_attachment=True, download_name="coordinates.csv", mimetype="text/csv")

if __name__ == "__main__":
    app.run(debug=True)
