using UnityEngine;
using TMPro;
using System.Collections;
using UnityEngine.Networking;

public class TempAPI : MonoBehaviour
{
    public TMP_Text titleText;
    public TMP_Text tempValueText;
    public TMP_Text unitText;
    public TMP_Text statusText;

    string apiUrl = "http://127.0.0.1:5000/api/v1/temp/latest";

    Coroutine apiCoroutine;

    public void StartAPI()
    {
        Debug.Log("Marker detected - starting API");

        titleText.text = "PATIENT TEMPERATURE";

        tempValueText.text = "--";
        unitText.text = "°C";
        statusText.text = "LOADING";

        if (apiCoroutine == null)
        {
            apiCoroutine = StartCoroutine(GetTemp());
        }
    }

    public void StopAPI()
    {
        Debug.Log("Marker lost - stopping API");

        if (apiCoroutine != null)
        {
            StopCoroutine(apiCoroutine);
            apiCoroutine = null;
        }

        tempValueText.text = "--";
        statusText.text = "--";
    }

    IEnumerator GetTemp()
    {
        while (true)
        {
            UnityWebRequest request = UnityWebRequest.Get(apiUrl);
            yield return request.SendWebRequest();

            if (request.result == UnityWebRequest.Result.Success)
            {
                string json = request.downloadHandler.text;
                Debug.Log("API RESPONSE: " + json);

                TempData data = JsonUtility.FromJson<TempData>(json);

                if (data != null)
                {
                    float temp = data.temperature;

                    tempValueText.text = temp.ToString("F1");
                    unitText.text = "°C";

                    // 🔥 Status + Color
                    if (temp < 36f)
                    {
                        statusText.text = "LOW";
                        statusText.color = new Color(0.2f, 0.6f, 1f); // blue glow
                    }
                    else if (temp > 37.5f)
                    {
                        statusText.text = "HIGH";
                        statusText.color = new Color(1f, 0.2f, 0.2f); // red glow
                    }
                    else
                    {
                        statusText.text = "NORMAL";
                        statusText.color = new Color(0f, 1f, 0.5f); // green glow
                    }
                }
                else
                {
                    tempValueText.text = "ERR";
                    statusText.text = "PARSE";
                    statusText.color = Color.yellow;
                }
            }
            else
            {
                Debug.Log("API ERROR: " + request.error);
                tempValueText.text = "ERR";
                statusText.text = "API";
                statusText.color = Color.yellow;
            }

            yield return new WaitForSeconds(0.3f);
        }
    }
}

[System.Serializable]
public class TempData
{
    public float temperature;
}