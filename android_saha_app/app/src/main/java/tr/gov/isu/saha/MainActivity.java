package tr.gov.isu.saha;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.app.PendingIntent;
import android.app.Notification;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.provider.MediaStore;
import android.webkit.CookieManager;
import android.webkit.GeolocationPermissions;
import android.webkit.PermissionRequest;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.EditText;
import android.widget.FrameLayout;

import androidx.core.content.FileProvider;

import org.json.JSONArray;
import org.json.JSONObject;

import java.io.BufferedReader;
import java.io.File;
import java.io.InputStreamReader;
import java.net.HttpURLConnection;
import java.net.URL;

public class MainActivity extends Activity {
    private WebView webView;
    private SharedPreferences prefs;
    private static final String KEY_URL = "server_url";
    private static final String KEY_LAST_NOTIFICATION = "last_notification_id";

    private static final int REQ_FILE = 1001;
    private static final int REQ_LOCATION = 1002;
    private static final int REQ_CAMERA = 1003;
    private static final int REQ_NOTIFICATIONS = 1004;
    private static final int REQ_WEB_CAMERA = 1005;
    private static final String CHANNEL_ID = "isu185_field_jobs";

    private ValueCallback<Uri[]> fileCallback;
    private PermissionRequest pendingWebCameraRequest;
    private Uri cameraUri;
    private GeolocationPermissions.Callback geoCallback;
    private String geoOrigin;

    private final Handler notificationHandler = new Handler(Looper.getMainLooper());
    private final Runnable notificationPoller = new Runnable() {
        @Override public void run() {
            pollNotifications();
            notificationHandler.postDelayed(this, 20000);
        }
    };

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        prefs = getSharedPreferences("isu185", MODE_PRIVATE);
        createNotificationChannel();

        webView = new WebView(this);
        webView.setLayoutParams(new FrameLayout.LayoutParams(
                FrameLayout.LayoutParams.MATCH_PARENT,
                FrameLayout.LayoutParams.MATCH_PARENT
        ));

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setGeolocationEnabled(true);
        settings.setBuiltInZoomControls(false);

        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(webView, true);

        webView.setWebViewClient(new WebViewClient());
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onPermissionRequest(PermissionRequest request) {
                boolean wantsCamera = false;
                for (String resource : request.getResources()) {
                    if (PermissionRequest.RESOURCE_VIDEO_CAPTURE.equals(resource)) {
                        wantsCamera = true;
                        break;
                    }
                }

                if (!wantsCamera) {
                    request.deny();
                    return;
                }

                if (checkSelfPermission(Manifest.permission.CAMERA)
                        == PackageManager.PERMISSION_GRANTED) {
                    request.grant(new String[]{PermissionRequest.RESOURCE_VIDEO_CAPTURE});
                } else {
                    pendingWebCameraRequest = request;
                    requestPermissions(
                            new String[]{Manifest.permission.CAMERA},
                            REQ_WEB_CAMERA
                    );
                }
            }

            @Override
            public void onGeolocationPermissionsShowPrompt(
                    String origin,
                    GeolocationPermissions.Callback callback
            ) {
                if (hasLocationPermission()) {
                    callback.invoke(origin, true, false);
                } else {
                    geoOrigin = origin;
                    geoCallback = callback;
                    requestPermissions(
                            new String[]{
                                    Manifest.permission.ACCESS_FINE_LOCATION,
                                    Manifest.permission.ACCESS_COARSE_LOCATION
                            },
                            REQ_LOCATION
                    );
                }
            }

            @Override
            public boolean onShowFileChooser(
                    WebView webView,
                    ValueCallback<Uri[]> filePathCallback,
                    FileChooserParams fileChooserParams
            ) {
                if (fileCallback != null) fileCallback.onReceiveValue(null);
                fileCallback = filePathCallback;
                openImageChooser();
                return true;
            }
        });

        setContentView(webView);
        requestNotificationPermissionIfNeeded();

        String saved = prefs.getString(KEY_URL, "");
        if (saved == null || saved.trim().isEmpty()) {
            askServerUrl();
        } else {
            webView.loadUrl(normalize(saved));
        }

        notificationHandler.postDelayed(notificationPoller, 12000);
    }

    private boolean hasLocationPermission() {
        return checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION)
                == PackageManager.PERMISSION_GRANTED
                || checkSelfPermission(Manifest.permission.ACCESS_COARSE_LOCATION)
                == PackageManager.PERMISSION_GRANTED;
    }

    private String normalize(String value) {
        String url = value.trim();
        if (!url.startsWith("http://") && !url.startsWith("https://")) {
            url = "http://" + url;
        }
        if (!url.endsWith("/")) url += "/";
        if (!url.contains("/mobil/saha/")) url += "mobil/saha/";
        return url;
    }

    private void askServerUrl() {
        final EditText input = new EditText(this);
        input.setHint("Örn. 192.168.1.25:8000");
        input.setSingleLine(true);

        new AlertDialog.Builder(this)
                .setTitle("İSU 185 Sunucu Adresi")
                .setMessage("Bilgisayar ve telefon aynı ağdayken PC'nin IPv4 adresini ve 8000 portunu girin.")
                .setView(input)
                .setCancelable(false)
                .setPositiveButton("Bağlan", (dialog, which) -> {
                    String value = input.getText().toString().trim();
                    prefs.edit().putString(KEY_URL, value).apply();
                    webView.loadUrl(normalize(value));
                })
                .show();
    }

    private void openImageChooser() {
        Intent galleryIntent = new Intent(Intent.ACTION_GET_CONTENT);
        galleryIntent.addCategory(Intent.CATEGORY_OPENABLE);
        galleryIntent.setType("image/*");

        Intent cameraIntent = null;
        if (checkSelfPermission(Manifest.permission.CAMERA) == PackageManager.PERMISSION_GRANTED) {
            try {
                File photo = File.createTempFile("isu185_", ".jpg", getCacheDir());
                cameraUri = FileProvider.getUriForFile(
                        this,
                        getPackageName() + ".fileprovider",
                        photo
                );
                cameraIntent = new Intent(MediaStore.ACTION_IMAGE_CAPTURE);
                cameraIntent.putExtra(MediaStore.EXTRA_OUTPUT, cameraUri);
                cameraIntent.addFlags(
                        Intent.FLAG_GRANT_WRITE_URI_PERMISSION
                                | Intent.FLAG_GRANT_READ_URI_PERMISSION
                );
            } catch (Exception ignored) {
                cameraIntent = null;
            }
        } else {
            requestPermissions(new String[]{Manifest.permission.CAMERA}, REQ_CAMERA);
        }

        Intent chooser = Intent.createChooser(galleryIntent, "Saha Fotoğrafı");
        if (cameraIntent != null) {
            chooser.putExtra(Intent.EXTRA_INITIAL_INTENTS, new Intent[]{cameraIntent});
        }
        startActivityForResult(chooser, REQ_FILE);
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        super.onActivityResult(requestCode, resultCode, data);
        if (requestCode != REQ_FILE || fileCallback == null) return;

        Uri[] result = null;
        if (resultCode == RESULT_OK) {
            if (data != null && data.getData() != null) {
                result = new Uri[]{data.getData()};
            } else if (cameraUri != null) {
                result = new Uri[]{cameraUri};
            }
        }
        fileCallback.onReceiveValue(result);
        fileCallback = null;
        cameraUri = null;
    }

    @Override
    public void onRequestPermissionsResult(
            int requestCode,
            String[] permissions,
            int[] grantResults
    ) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults);

        if (requestCode == REQ_LOCATION && geoCallback != null) {
            boolean allowed = hasLocationPermission();
            geoCallback.invoke(geoOrigin, allowed, false);
            geoCallback = null;
            geoOrigin = null;
        }

        if (requestCode == REQ_WEB_CAMERA && pendingWebCameraRequest != null) {
            boolean allowed = checkSelfPermission(Manifest.permission.CAMERA)
                    == PackageManager.PERMISSION_GRANTED;
            if (allowed) {
                pendingWebCameraRequest.grant(
                        new String[]{PermissionRequest.RESOURCE_VIDEO_CAPTURE}
                );
            } else {
                pendingWebCameraRequest.deny();
            }
            pendingWebCameraRequest = null;
        }
    }

    private void createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            NotificationChannel channel = new NotificationChannel(
                    CHANNEL_ID,
                    "İSU 185 Saha İş Emirleri",
                    NotificationManager.IMPORTANCE_HIGH
            );
            channel.setDescription("Yeni iş emri ve şef geri gönderme bildirimleri");
            getSystemService(NotificationManager.class).createNotificationChannel(channel);
        }
    }

    private void requestNotificationPermissionIfNeeded() {
        if (Build.VERSION.SDK_INT >= 33
                && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED) {
            requestPermissions(
                    new String[]{Manifest.permission.POST_NOTIFICATIONS},
                    REQ_NOTIFICATIONS
            );
        }
    }

    private String notificationApiUrl() {
        String current = webView.getUrl();
        if (current == null || current.isEmpty()) return null;
        Uri uri = Uri.parse(current);
        if (uri.getHost() == null) return null;
        StringBuilder base = new StringBuilder();
        base.append(uri.getScheme()).append("://").append(uri.getHost());
        if (uri.getPort() != -1) base.append(":").append(uri.getPort());
        base.append("/api/mobil/bildirimler/");
        return base.toString();
    }

    private void pollNotifications() {
        String api = notificationApiUrl();
        if (api == null) return;
        String cookie = CookieManager.getInstance().getCookie(webView.getUrl());
        if (cookie == null || cookie.isEmpty()) return;

        new Thread(() -> {
            HttpURLConnection connection = null;
            try {
                connection = (HttpURLConnection) new URL(api).openConnection();
                connection.setRequestMethod("GET");
                connection.setRequestProperty("Cookie", cookie);
                connection.setRequestProperty("X-Requested-With", "AndroidWebView");
                connection.setConnectTimeout(5000);
                connection.setReadTimeout(5000);

                if (connection.getResponseCode() != 200) return;

                BufferedReader reader = new BufferedReader(
                        new InputStreamReader(connection.getInputStream())
                );
                StringBuilder json = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) json.append(line);
                reader.close();

                JSONObject root = new JSONObject(json.toString());
                JSONArray items = root.optJSONArray("bildirimler");
                if (items == null || items.length() == 0) return;

                int currentMax = 0;
                JSONObject newest = null;
                for (int i = 0; i < items.length(); i++) {
                    JSONObject item = items.getJSONObject(i);
                    int id = item.optInt("id", 0);
                    if (id > currentMax) {
                        currentMax = id;
                        newest = item;
                    }
                }

                int last = prefs.getInt(KEY_LAST_NOTIFICATION, 0);
                if (last == 0) {
                    prefs.edit().putInt(KEY_LAST_NOTIFICATION, currentMax).apply();
                    return;
                }

                if (currentMax > last && newest != null) {
                    prefs.edit().putInt(KEY_LAST_NOTIFICATION, currentMax).apply();
                    String title = newest.optString("baslik", "İSU 185 Yeni İş");
                    String message = newest.optString("mesaj", "");
                    int notificationId = currentMax;
                    runOnUiThread(() -> showLocalNotification(notificationId, title, message));
                }
            } catch (Exception ignored) {
            } finally {
                if (connection != null) connection.disconnect();
            }
        }).start();
    }

    private void showLocalNotification(int id, String title, String message) {
        if (Build.VERSION.SDK_INT >= 33
                && checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS)
                != PackageManager.PERMISSION_GRANTED) return;

        Intent intent = new Intent(this, MainActivity.class);
        intent.setFlags(Intent.FLAG_ACTIVITY_SINGLE_TOP | Intent.FLAG_ACTIVITY_CLEAR_TOP);
        PendingIntent pendingIntent = PendingIntent.getActivity(
                this,
                0,
                intent,
                PendingIntent.FLAG_UPDATE_CURRENT | PendingIntent.FLAG_IMMUTABLE
        );

        Notification.Builder builder = Build.VERSION.SDK_INT >= Build.VERSION_CODES.O
                ? new Notification.Builder(this, CHANNEL_ID)
                : new Notification.Builder(this);

        builder.setContentTitle(title)
                .setContentText(message)
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentIntent(pendingIntent)
                .setAutoCancel(true)
                .setPriority(Notification.PRIORITY_HIGH);

        NotificationManager manager =
                (NotificationManager) getSystemService(NOTIFICATION_SERVICE);
        manager.notify(id, builder.build());
    }

    @Override
    protected void onDestroy() {
        notificationHandler.removeCallbacks(notificationPoller);
        if (webView != null) webView.destroy();
        super.onDestroy();
    }

    @Override
    public void onBackPressed() {
        if (webView != null && webView.canGoBack()) webView.goBack();
        else super.onBackPressed();
    }
}
