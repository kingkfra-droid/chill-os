package com.kingkfra.chillos;

import android.content.Context;

import java.io.File;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public final class Bridge {

    public interface Callback {
        void onUpdate(State state);
    }

    public static final class State {
        public final boolean bridgeReady;
        public final boolean prootReady;
        public final boolean rootfsReady;
        public final String message;

        public State(boolean bridgeReady,
                     boolean prootReady,
                     boolean rootfsReady,
                     String message) {
            this.bridgeReady = bridgeReady;
            this.prootReady = prootReady;
            this.rootfsReady = rootfsReady;
            this.message = message;
        }
    }

    private static final ExecutorService EXECUTOR =
            Executors.newSingleThreadExecutor();

    private Bridge() {
    }

    public static void start(Context context, Callback callback) {
        Context app = context.getApplicationContext();

        EXECUTOR.execute(() -> {
            try {
                File base = new File(app.getFilesDir(), "chillos");
                File workspace = new File(base, "workspace");
                File rootfs = new File(base, "rootfs");

                if (!workspace.exists() && !workspace.mkdirs()) {
                    throw new Exception("Unable to create ChillOS workspace");
                }

                if (!rootfs.exists() && !rootfs.mkdirs()) {
                    throw new Exception("Unable to create RootFS directory");
                }

                Process process = new ProcessBuilder(
                        "/system/bin/sh",
                        "-c",
                        "printf 'CHILLOS_BRIDGE_OK\\n'"
                ).redirectErrorStream(true).start();

                boolean finished = process.waitFor(5, TimeUnit.SECONDS);

                if (!finished) {
                    process.destroyForcibly();
                    throw new Exception("Bridge shell timed out");
                }

                if (process.exitValue() != 0) {
                    throw new Exception("Android shell unavailable");
                }

                /*
                 * The APK sandbox is separate from Termux.
                 *
                 * Therefore we do NOT falsely claim that PRoot or the
                 * Termux ChillOS RootFS is available here. Those require
                 * the next integration layer.
                 */
                post(callback, new State(
                        true,
                        false,
                        false,
                        "Bridge initialized successfully.\n"
                                + "APK workspace: READY\n"
                                + "Android shell: READY\n"
                                + "PRoot: NOT BUNDLED\n"
                                + "RootFS: NOT BUNDLED\n"
                                + "Termux integration: NEXT STAGE"
                ));

            } catch (Exception e) {
                post(callback, new State(
                        false,
                        false,
                        false,
                        "Bridge initialization failed:\n"
                                + e.getMessage()
                ));
            }
        });
    }

    public static void doctor(Context context, Callback callback) {
        Context app = context.getApplicationContext();

        EXECUTOR.execute(() -> {
            File base = new File(app.getFilesDir(), "chillos");
            File workspace = new File(base, "workspace");
            File rootfs = new File(base, "rootfs");

            boolean workspaceReady = workspace.isDirectory();
            boolean rootfsReady = rootfs.isDirectory();

            post(callback, new State(
                    workspaceReady,
                    false,
                    rootfsReady && false,
                    "APK diagnostic complete.\n"
                            + "Workspace: "
                            + (workspaceReady ? "READY" : "MISSING")
                            + "\nRootFS directory: "
                            + (rootfsReady ? "READY" : "MISSING")
                            + "\nPRoot: NOT BUNDLED"
                            + "\nTermux bridge: NEXT STAGE"
            ));
        });
    }

    private static void post(Callback callback, State state) {
        if (callback == null) {
            return;
        }

        new android.os.Handler(
                android.os.Looper.getMainLooper()
        ).post(() -> callback.onUpdate(state));
    }
}
