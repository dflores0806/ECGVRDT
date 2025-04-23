package es.unex.spilab.ecgvrdtdroid

import android.app.Activity
import android.os.Bundle
import android.widget.*
import android.util.Log
import androidx.appcompat.app.AppCompatActivity
import androidx.navigation.ui.AppBarConfiguration
import org.tensorflow.lite.Interpreter
import java.io.File
import java.io.FileOutputStream
import java.net.HttpURLConnection
import java.net.URL
import java.nio.channels.FileChannel
import kotlin.random.Random
import androidx.appcompat.widget.Toolbar

class MainActivity :  AppCompatActivity() {

    private lateinit var interpreter: Interpreter
    private lateinit var resultTextView: TextView

    private lateinit var hrInput: EditText
    private lateinit var prInput: EditText
    private lateinit var qrsInput: EditText
    private lateinit var stInput: EditText
    private lateinit var qtcInput: EditText
    private lateinit var axisInput: EditText
    private lateinit var rhythmSpinner: Spinner
    private lateinit var tWaveSpinner: Spinner
    private lateinit var urlEditText: EditText
    private lateinit var diagnosisSpinner: Spinner

    private val rhythms = arrayOf("Sinus", "Bradycardia", "Tachycardia", "Atrial Fibrillation")
    private val tWaves = arrayOf("Normal", "Inverted", "Peaked", "Flattened")

    private val classLabels = arrayOf(
        "Normal", "Bradycardia", "Tachycardia",
        "Atrial Fibrillation", "Myocardial Infaction", "Hearth Block"
    )

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        // Initialize the toolbar
        val toolbar: Toolbar = findViewById(R.id.toolbar)
        setSupportActionBar(toolbar)  // Set the toolbar as the action bar
        supportActionBar?.title = "ECG Digital Twin Mentor"  // Optional: set the title

        resultTextView = findViewById(R.id.resultTextView)
        val generateecgButton: Button = findViewById(R.id.generateecgButton)
        val predictButton: Button = findViewById(R.id.predictButton)
        val updateButton: Button = findViewById(R.id.updateButton)
        val exampleButton: Button = findViewById(R.id.exampleButton)
        urlEditText = findViewById(R.id.urlEditText)

        diagnosisSpinner = findViewById(R.id.diagnosisSpinner)

        // Set up the spinner for the user's diagnosis
        val diagnosisAdapter = ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, classLabels)
        diagnosisSpinner.adapter = diagnosisAdapter

        hrInput = findViewById(R.id.hrInput)
        prInput = findViewById(R.id.prInput)
        qrsInput = findViewById(R.id.qrsInput)
        stInput = findViewById(R.id.stInput)
        qtcInput = findViewById(R.id.qtcInput)
        axisInput = findViewById(R.id.axisInput)
        rhythmSpinner = findViewById(R.id.rhythmSpinner)
        tWaveSpinner = findViewById(R.id.tWaveSpinner)

        rhythmSpinner.adapter = ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, rhythms)
        tWaveSpinner.adapter = ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, tWaves)

        interpreter = loadModelFromAssets()

        // Load the model at the start
        predictButton.setOnClickListener {
            try {
                // Define the values for normalization
                val hrMin = 40f
                val hrMax = 180f

                val prMin = 120f
                val prMax = 300f

                val qrsMin = 60f
                val qrsMax = 120f

                val stMin = -0.5f
                val stMax = 2.0f

                val qtcMin = 300f
                val qtcMax = 500f

                val axisMin = -30f
                val axisMax = 180f

                // Get the values from the EditTexts and normalize them
                val hr = cleanInput(hrInput.text.toString())?.let { (it - hrMin) / (hrMax - hrMin) }
                val pr = cleanInput(prInput.text.toString())?.let { (it - prMin) / (prMax - prMin) }
                val qrs = cleanInput(qrsInput.text.toString())?.let { (it - qrsMin) / (qrsMax - qrsMin) }
                val st = cleanInput(stInput.text.toString())?.let { (it - stMin) / (stMax - stMin) }
                val qtc = cleanInput(qtcInput.text.toString())?.let { (it - qtcMin) / (qtcMax - qtcMin) }
                val axis = cleanInput(axisInput.text.toString())?.let { (it - axisMin) / (axisMax - axisMin) }

                // Verify that the values are not null
                if (hr == null || pr == null || qrs == null || st == null || qtc == null || axis == null) {
                    resultTextView.text = "Please fill in all fields with valid numbers."
                    Log.e("MainActivity", "Error: Invalid input detected!")
                    return@setOnClickListener
                }

                // Get the values of the spinners as numerical indices
                val rhythmIndex = rhythmSpinner.selectedItemPosition.toFloat()
                val tWaveIndex = tWaveSpinner.selectedItemPosition.toFloat()

                // Show the input values for debugging
                Log.d("MainActivity", "Normalized input values: HR=$hr, PR=$pr, QRS=$qrs, ST=$st, QTc=$qtc, Axis=$axis")
                Log.d("MainActivity", "Spinner values: Rhythm=$rhythmIndex, TWave=$tWaveIndex")

                // **Make sure to pass the input as [1, 8]**
                val inputData = Array(1) { floatArrayOf(
                    hr, pr, qrs, st, qtc, axis,
                    rhythmIndex, tWaveIndex
                )}

                // Log input data to model
                Log.d("MainActivity", "Input data to model: ${inputData[0].joinToString(", ")}")

                // Run inference with TensorFlow Lite
                val output = Array(1) { FloatArray(classLabels.size) }
                interpreter.run(inputData, output)

                // Log to check the model's output
                Log.d("MainActivity", "Model output: ${output[0].joinToString(", ")}")

                // Get the predicted class with the highest confidence
                val maxIdx = output[0].indices.maxByOrNull { output[0][it] } ?: -1
                val confidence = output[0][maxIdx] * 100
                val resultText = "Predicted class: ${classLabels[maxIdx]}\nConfidence: %.2f%%".format(confidence)
                resultTextView.text = resultText

                // Get the diagnosis selected by the user
                val selectedDiagnosis = diagnosisSpinner.selectedItem.toString()

                // Get the input values
                val hrV = cleanInput(hrInput.text.toString())
                val prV = cleanInput(prInput.text.toString())
                val qrsV = cleanInput(qrsInput.text.toString())
                val stV = cleanInput(stInput.text.toString())
                val qtcV = cleanInput(qtcInput.text.toString())
                val axisV = cleanInput(axisInput.text.toString())

                // Update the ECGView with the new values
                val ecgView = findViewById<ECGView>(R.id.ecgView)
                ecgView.heartRate = hrV ?: 75f
                ecgView.prInterval = prV ?: 160f
                ecgView.qrsDuration = qrsV ?: 90f
                ecgView.stSegment = stV ?: 1f
                ecgView.qtcInterval = qtcV ?: 380f

                // Redraw the ECG
                ecgView.invalidate()

                // Compare the prediction with the selected diagnosis
                val predictedClass = classLabels[maxIdx]
                if (predictedClass == selectedDiagnosis) {
                    resultTextView.text = resultText + "\n\nCorrect prediction!"
                } else {
                    resultTextView.text = resultText + "\n\nIncorrect! Your Diagnosis: $selectedDiagnosis"
                }

            } catch (e: Exception) {
                resultTextView.text = "Error: ${e.message}"
                Log.e("MainActivity", "Error during prediction: ${e.message}")
            }
        }

        generateecgButton.setOnClickListener {
            // Get the values of the input parameters
            val hr = cleanInput(hrInput.text.toString())
            val pr = cleanInput(prInput.text.toString())
            val qrs = cleanInput(qrsInput.text.toString())
            val st = cleanInput(stInput.text.toString())
            val qtc = cleanInput(qtcInput.text.toString())
            val axis = cleanInput(axisInput.text.toString())

            // Update the ECGView with the new values
            val ecgView = findViewById<ECGView>(R.id.ecgView)
            ecgView.heartRate = hr ?: 75f
            ecgView.prInterval = pr ?: 160f
            ecgView.qrsDuration = qrs ?: 90f
            ecgView.stSegment = st ?: 1f
            ecgView.qtcInterval = qtc ?: 380f

            // Redraw the ECG
            ecgView.invalidate()
        }

        // Update model from URL
        updateButton.setOnClickListener {
            val url = urlEditText.text.toString()
            downloadModel(url)
        }

        // Button to load random example values
        exampleButton.setOnClickListener {
            loadExampleValues()
        }
    }

    private fun loadModelFromAssets(): Interpreter {
        val assetFileDescriptor = assets.openFd("ecg_model.tflite")
        val inputStream = assetFileDescriptor.createInputStream()
        val fileChannel = inputStream.channel
        val startOffset = assetFileDescriptor.startOffset
        val declaredLength = assetFileDescriptor.declaredLength
        val buffer = fileChannel.map(FileChannel.MapMode.READ_ONLY, startOffset, declaredLength)
        return Interpreter(buffer)
    }

    private fun downloadModel(urlString: String) {
        // Logic to download the model from the URL and update it
        Thread {
            try {
                val url = URL(urlString)
                val connection = url.openConnection() as HttpURLConnection
                connection.connect()
                val input = connection.inputStream
                val outputFile = File(filesDir, "ecg_model.tflite")
                val output = FileOutputStream(outputFile)
                val buffer = ByteArray(1024)
                var bytesRead: Int
                while (input.read(buffer).also { bytesRead = it } != -1) {
                    output.write(buffer, 0, bytesRead)
                }
                output.close()
                input.close()
                runOnUiThread {
                    resultTextView.text = "Model updated successfully!"
                    interpreter = Interpreter(outputFile)
                }
            } catch (e: Exception) {
                runOnUiThread {
                    resultTextView.text = "Model update failed: ${e.message}"
                }
            }
        }.start()
    }

    private fun loadExampleValues() {
        // Assign random values to the EditTexts with dot as decimal separator
        hrInput.setText("%.1f".format(60 + Random.nextFloat() * 60).replace(',', '.'))
        prInput.setText("%.1f".format(120 + Random.nextFloat() * 80).replace(',', '.'))
        qrsInput.setText("%.1f".format(80 + Random.nextFloat() * 40).replace(',', '.'))
        stInput.setText("%.2f".format(-1 + Random.nextFloat() * 3).replace(',', '.'))
        qtcInput.setText("%.1f".format(360 + Random.nextFloat() * 100).replace(',', '.'))
        axisInput.setText("%.1f".format(-30 + Random.nextFloat() * 150).replace(',', '.'))

        rhythmSpinner.setSelection(Random.nextInt(rhythms.size))
        tWaveSpinner.setSelection(Random.nextInt(tWaves.size))

        Log.d("MainActivity", "Example values set for inputs and spinners.")
    }

    // Function to clean the input values before converting them to Float
    private fun cleanInput(input: String): Float? {
        val cleanedInput = input.trim()  // Clean whitespace
        return if (cleanedInput.isNotEmpty()) {
            cleanedInput.replace(',', '.').toFloatOrNull()  // Replace comma with dot
        } else {
            null  // Return null if the value is empty
        }
    }
}
