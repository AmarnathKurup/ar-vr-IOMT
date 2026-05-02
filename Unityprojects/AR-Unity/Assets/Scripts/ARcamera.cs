using UnityEngine;
using Vuforia;

public class ARCamera : MonoBehaviour
{
    void Start()
    {
        if (VuforiaBehaviour.Instance != null)
        {
            VuforiaBehaviour.Instance.CameraDevice.SetFocusMode(
                FocusMode.FOCUS_MODE_CONTINUOUSAUTO
            );
        }
    }
}