package com.kingkfra.chillos;

import android.app.Activity;
import android.os.Bundle;
import android.widget.Button;
import android.widget.TextView;

public class MainActivity extends Activity {

    private TextView status;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        setContentView(R.layout.activity_main);

        status = findViewById(R.id.status);

        Button startButton = findViewById(R.id.startButton);
        Button doctorButton = findViewById(R.id.doctorButton);

        detectEnvironment();

        startButton.setOnClickListener(v ->
            status.setText(
                "ChillOS launcher\n\n" +
                "Android frontend: READY\n" +
                "ChillOS bridge: NEXT STAGE"
            )
        );

        doctorButton.setOnClickListener(v ->
            detectEnvironment()
        );
    }

    private void detectEnvironment() {

        String abi = "unknown";

        if (android.os.Build.SUPPORTED_ABIS.length > 0) {
            abi = android.os.Build.SUPPORTED_ABIS[0];
        }

        StringBuilder result = new StringBuilder();

        result.append("CHILLOS ENVIRONMENT\n\n");
        result.append("Android : ")
              .append(android.os.Build.VERSION.RELEASE)
              .append("\n");

        result.append("Device  : ")
              .append(android.os.Build.MODEL)
              .append("\n");

        result.append("ABI     : ")
              .append(abi)
              .append("\n\n");

        result.append("APK frontend : READY\n");
        result.append("ChillOS core : READY\n");
        result.append("Bridge       : PENDING\n");
        result.append("PRoot        : PENDING\n");
        result.append("RootFS       : PENDING\n");

        status.setText(result.toString());
    }
}
