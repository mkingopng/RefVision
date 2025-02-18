### Detailed Instructions for Labeling and Annotation in CVAT

Here’s a step-by-step guide to help you set up and use CVAT for labeling and annotating powerlifting videos based on the provided ontology.

---

### **1. Setting Up CVAT**

#### **Install CVAT**
1. **Cloud Service**:
   - Go to [CVAT.org](https://cvat.org/) and create an account.
   - Use their hosted version (simpler and faster for most users).

2. **Self-hosted Version**:
   - Follow [CVAT installation instructions](https://opencv.github.io/cvat/docs/administration/installation/) for local deployment using Docker.

---

### **2. Upload the Ontology to CVAT**

1. **Log in** to CVAT.
2. Navigate to the **Projects** tab and click **+ Create Project**.
3. Name your project (e.g., "Powerlifting Annotation").
4. In the project settings, go to the **Labels** section.
5. **Import the Ontology**:
   - Copy the JSON ontology provided earlier.
   - Paste it into the **Label Configuration Editor**.
   - Click **Save** to load the labels and attributes into the project.

---

### **3. Upload Videos for Annotation**

1. **Create a Task**:
   - Go to the **Tasks** tab and click **+ Create Task**.
   - Name the task (e.g., "Squat Lifts - Event 001").
   - Assign it to a project (e.g., "Powerlifting Annotation").

2. **Upload Videos**:
   - Drag and drop video files or provide a URL for video hosting (e.g., from YouTube or cloud storage like AWS S3).
   - Choose **Video** as the file type.

3. Click **Submit** to create the task.

---

### **4. Annotate Videos**

#### **Start Annotation**
1. Open the task you created.
2. Click **Open** to launch the CVAT annotation interface.

#### **Annotation Interface Overview**
- **Canvas**: Displays the video frames.
- **Player Controls**:
  - Play, pause, and navigate frame-by-frame.
  - Use the timeline slider to jump to specific parts of the video.
- **Annotation Toolbar**:
  - Tools for drawing bounding boxes, polygons, points, or other regions of interest.
  - Use the right panel to manage labels and attributes.

---

### **5. Labeling and Annotating**

#### **Label Metadata**
1. Go to the **Attributes Panel** on the right side.
2. Fill out metadata attributes for the video:
   - `lift_type`: Select `Squat`, `BenchPress`, or `Deadlift`.
   - `lifter_id`: Enter the lifter's unique ID.
   - `attempt_number`: Input the attempt number (1, 2, or 3).
   - `division`: Choose `Raw`, `Wraps`, or `Single-Ply`.
   - `weight`: Enter the weight lifted in kilograms.
   - `event_id`: Enter the event ID or name.

#### **Annotate Specific Frames**
1. **Keyframe Annotations**:
   - Pause at critical points in the lift (e.g., start, descent, completion).
   - Annotate specific moments for attributes like:
     - `bar_position`: `<3cm` or `>3cm` below posterior deltoids.
     - `knees_locked_start`: Check if the knees are locked at the start.
     - `depth`: Determine squat depth (`below_parallel`, `at_parallel`, `above_parallel`).

2. **Attribute Selection**:
   - Click the label for the lift (e.g., `Squat`) on the right panel.
   - Select or input values for attributes:
     - Checkboxes for binary states (e.g., `knees_locked_start`).
     - Drop-down menus for categorical attributes (e.g., `stance_width`).

3. **Use Object Tracking** (Optional):
   - If tracking the lifter’s bar path or motion across frames, use CVAT’s object tracking tools:
     - Draw a bounding box around the bar or lifter.
     - Enable interpolation to track movements across frames.

4. **Frame-by-Frame Review**:
   - Use the frame navigation tools to annotate the entire lift sequence.
   - Ensure annotations are consistent for all critical phases (setup, execution, completion).

---

### **6. Save Annotations**

1. Click **Save** regularly to avoid losing progress.
2. Review the annotation timeline for completeness.

---

### **7. Export Annotations**

1. Go to the **Task Page**.
2. Click **Export**.
3. Choose the desired format (e.g., **COCO**, **Pascal VOC**, or **CVAT JSON**).
   - **CVAT JSON**: Retains all labels and attributes for further use.
   - **Custom Formats**: Can be mapped for integration with your video analysis system.

---

### **8. Best Practices**

- **Annotate in Teams**:
  - Assign tasks to multiple team members to speed up annotation.
  - Use CVAT’s built-in reviewer roles to cross-check annotations.

- **Use Consistent Guidelines**:
  - Provide clear instructions to annotators for interpreting attributes (e.g., what qualifies as `below_parallel` depth).

- **Start Small**:
  - Annotate a small batch of videos first to validate the ontology and refine workflows.

- **Automation**:
  - Use CVAT’s semi-automatic tools (e.g., AI-assisted bounding box creation) to reduce manual work.

---

### **9. Training AI with Annotations**
Once the dataset is annotated:
1. Export annotations in a format compatible with your machine learning framework (e.g., TensorFlow, PyTorch).
2. Use the labeled data to train a model for video analysis:
   - Frame classification for phases (setup, execution, completion).
   - Object tracking for bar/lifter movements.
   - Attribute prediction for rule evaluation.

---

By following these steps, you’ll create a high-quality labelled dataset that aligns perfectly with your business logic and evaluation criteria. This setup ensures accurate and consistent annotations, crucial for developing reliable video analysis models.