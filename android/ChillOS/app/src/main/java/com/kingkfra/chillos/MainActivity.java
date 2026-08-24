package com.kingkfra.chillos;

import android.app.Activity;
import android.os.Bundle;
import android.os.Build;
import android.widget.Button;
import android.widget.TextView;

public class MainActivity extends Activity {

    private TextView status;
    private Button startButton;
    private Button doctorButton;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        setContentView(R.layout.activity_main);

        status = findViewById(R.id.status);
        startButton = findViewById(R.id.startButton);
        doctorButton = findViewById(R.id.doctorButton);

        detectEnvironment();

        startButton.setOnClickListener(v -> startChillOS());

        doctorButton.setOnClickListener(v -> runDoctor());
    }

    private void detectEnvironment() {
        String abi = "unknown";

        if (Build.SUPPORTED_ABIS.length > 0) {
            abi = Build.SUPPORTED_ABIS[0];
        }

        StringBuilder result = new StringBuilder();

        result.append("CHILLOS ENVIRONMENT\n\n");

        result.append("Android : ")
                .append(Build.VERSION.RELEASE)
                .append("\n");

        result.append("Device  : ")
                .append(Build.MODEL)
                .append("\n");

        result.append("ABI     : ")
                .append(abi)
                .append("\n\n");

        result.append("APK frontend : READY\n");
        result.append("ChillOS core : APK BRIDGE\n");
        result.append("Bridge       : READY\n");
        result.append("PRoot        : PENDING\n");
        result.append("RootFS       : PENDING\n");

        status.setText(result.toString());
    }

    private void startChillOS() {
        startButton.setEnabled(false);
        doctorButton.setEnabled(false);

        status.setText(
                "CHILLOS STARTING...\n\n"
                        + "Initializing Android bridge...\n"
                        + "Preparing workspace..."
        );

        Bridge.start(this, state -> {
            startButton.setEnabled(true);
            doctorButton.setEnabled(true);

            StringBuilder result = new StringBuilder();

            result.append("CHILLOS\n\n");
            result.append("APK frontend : READY\n");
            result.append("Bridge       : ")
                    .append(state.bridgeReady ? "READY" : "FAILED")
                    .append("\n");
            result.append("PRoot        : ")
                    .append(state.prootReady ? "READY" : "PENDING")
                    .append("\n");
            result.append("RootFS       : ")
                    .append(state.rootfsReady ? "READY" : "PENDING")
                    .append("\n\n");
            result.append(state.message);

            status.setText(result.toString());
        });
    }

    private void runDoctor() {
        startButton.setEnabled(false);
        doctorButton.setEnabled(false);

        status.setText(
                "CHILLOS DOCTOR\n\n"
                        + "Scanning APK environment..."
        );

        Bridge.doctor(this, state -> {
            startButton.setEnabled(true);
            doctorButton.setEnabled(true);

            status.setText(
                    "CHILLOS DOCTOR\n\n"
                            + "Bridge       : "
                            + (state.bridgeReady ? "READY" : "NOT READY")
                            + "\n"
                            + "PRoot        : "
                            + (state.prootReady ? "READY" : "PENDING")
                            + "\n"
                            + "RootFS       : "
                            + (state.rootfsReady ? "READY" : "PENDING")
                            + "\n\n"
                            + state.message
            );
        });
    }
}
