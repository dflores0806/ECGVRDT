package es.unex.spilab.ecgvrdtdroid

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.util.AttributeSet
import android.view.View
import kotlin.math.PI
import kotlin.math.cos
import kotlin.math.sin

// Custom class to draw an ECG based on the provided parameters
class ECGView(context: Context, attrs: AttributeSet?) : View(context, attrs) {

    // ECG parameters that will influence the shape of the drawn ECG
    var heartRate: Float = 75f    // Heart rate (BPM)
    var prInterval: Float = 160f  // PR interval (ms)
    var qrsDuration: Float = 90f  // QRS duration (ms)
    var stSegment: Float = 1f     // ST segment (normalized)
    var qtcInterval: Float = 380f // QTc interval (ms)

    // Paint object to draw on the Canvas
    private val paint = Paint().apply {
        color = Color.BLACK
        strokeWidth = 3f
        isAntiAlias = true
    }

    // Method to draw the ECG
    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)

        // Get the dimensions of the view
        val width = width.toFloat()
        val height = height.toFloat()

        // Spacing between points to simulate the ECG
        val xSpacing = width / 100
        var currentX = 0f

        // If the parameters haven't been set, draw a straight line (simulate a flat ECG)
        if (heartRate == 75f && prInterval == 160f && qrsDuration == 90f && qtcInterval == 380f) {
            // Draw a straight line (simulating a flat ECG)
            canvas.drawLine(0f, height / 2, width, height / 2, paint)
        } else {
            // Simulate the P, QRS, and T waves based on the parameters

            // Heart rate (BPM) to control the distance between the waves
            val timeInterval = 60f / heartRate

            // Adjust amplitudes and frequencies for the P, QRS, and T waves
            val pAmplitude = height * 0.1f
            val pFrequency = 2 * PI / timeInterval
            val qrsAmplitude = height * 0.3f
            val qrsFrequency = 2 * PI / (qrsDuration / 1000f)
            val tAmplitude = height * 0.2f
            val tFrequency = 2 * PI / (qtcInterval / 1000f)

            // P wave: Represented by a sine wave, affected by the PR interval
            val pPhaseShift = prInterval / 1000f  // Shift by PR interval

            // Draw the P wave (atrial depolarization)
            var lastX = currentX
            var lastY = height / 2 + pAmplitude * sin(pFrequency * 0 + pPhaseShift).toFloat()
            for (i in 1 until 100) {
                val x = currentX + i * xSpacing
                val y = height / 2 + pAmplitude * sin(pFrequency * i + pPhaseShift).toFloat()
                canvas.drawLine(lastX, lastY, x, y, paint)
                lastX = x
                lastY = y
            }
            currentX += xSpacing * 100

            // Draw the Q wave (start of the QRS complex)
            lastX = currentX
            lastY = height / 2 + qrsAmplitude * cos(qrsFrequency * 0).toFloat()
            for (i in 1 until 30) {
                val x = currentX + i * xSpacing
                val y = height / 2 + qrsAmplitude * cos(qrsFrequency * i).toFloat()
                canvas.drawLine(lastX, lastY, x, y, paint)
                lastX = x
                lastY = y
            }
            currentX += xSpacing * 30

            // Draw the R wave (peak)
            lastX = currentX
            lastY = height / 2 - qrsAmplitude * cos(qrsFrequency * 0).toFloat()
            for (i in 1 until 30) {
                val x = currentX + i * xSpacing
                val y = height / 2 - qrsAmplitude * cos(qrsFrequency * i).toFloat()
                canvas.drawLine(lastX, lastY, x, y, paint)
                lastX = x
                lastY = y
            }
            currentX += xSpacing * 30

            // Draw the S wave (final ventricular depolarization)
            lastX = currentX
            lastY = height / 2 + qrsAmplitude * sin(qrsFrequency * 0).toFloat()
            for (i in 1 until 30) {
                val x = currentX + i * xSpacing
                val y = height / 2 + qrsAmplitude * sin(qrsFrequency * i).toFloat()
                canvas.drawLine(lastX, lastY, x, y, paint)
                lastX = x
                lastY = y
            }
            currentX += xSpacing * 30

            // Draw the T wave (ventricular repolarization)
            lastX = currentX
            lastY = height / 2 + tAmplitude * cos(tFrequency * 0).toFloat()
            for (i in 1 until 100) {
                val x = currentX + i * xSpacing
                val y = height / 2 + tAmplitude * cos(tFrequency * i).toFloat()
                canvas.drawLine(lastX, lastY, x, y, paint)
                lastX = x
                lastY = y
            }
        }
    }
}
