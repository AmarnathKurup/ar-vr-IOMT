using UnityEngine;
using TMPro;
using System.Collections;
using UnityEngine.Networking;

public class SensorAPI : MonoBehaviour
{
    public TMP_Text heartText;
    public TMP_Text spo2Text;

    string apiUrl = "http://127.0.0.1:5000/api/v1/max30100/latest";

    Coroutine apiCoroutine;

    // 🔥 Called when marker is detected
    public void StartAPI()
    {
        Debug.Log("Sensor Marker detected - starting API");

        heartText.text = "Fetching...";
        spo2Text.text = "Fetching...";

        if (apiCoroutine == null)
        {
            apiCoroutine = StartCoroutine(GetSensorData());
        }
    }

    // 🔥 Called when marker is lost
    public void StopAPI()
    {
        Debug.Log("Sensor Marker lost - stopping API");

        if (apiCoroutine != null)
        {
            StopCoroutine(apiCoroutine);
            apiCoroutine = null;
        }

        heartText.text = "--";
        spo2Text.text = "--";
    }

    IEnumerator GetSensorData()
    {
        while (true)
        {
            Debug.Log("Calling Sensor API...");

            UnityWebRequest request = UnityWebRequest.Get(apiUrl);
            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                string json = request.downloadHandler.text;

                Debug.Log("SENSOR API RESPONSE: " + json);

                SensorData data = JsonUtility.FromJson<SensorData>(json);

                if (data != null)
                {
                    heartText.text = "Heart: " + data.heart_rate + " bpm";
                    spo2Text.text = "SpO2: " + data.spo2 + " %";
                }
                else
                {
                    heartText.text = "Parse Error";
                    spo2Text.text = "Parse Error";
                }
            }
            else
            {
                Debug.Log("API ERROR: " + request.error);
                heartText.text = "API ERROR";
                spo2Text.text = "API ERROR";
            }

            yield return new WaitForSeconds(2);
        }
    }
}

[System.Serializable]
public class SensorData
{
    public int heart_rate;
    public int spo2;
}