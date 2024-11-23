#include <opencv2/opencv.hpp>
#include <iostream>

int main() {
    // Video parameters
    int frameWidth = 640;  // Video width
    int frameHeight = 480; // Video height
    int fps = 1;           // Frames per second (1 frame per second)
    int duration = 10;     // Video duration in seconds
    int codec = cv::VideoWriter::fourcc('X', '2', '6', '4'); // H.264 codec (requires FFmpeg)
    std::string videoFileName = "output.mp4"; // Name of the output video file

    // Create a VideoWriter object to write the video
    cv::VideoWriter videoWriter(videoFileName, codec, fps, cv::Size(frameWidth, frameHeight));
    if (!videoWriter.isOpened()) {
        std::cerr << "Failed to open the video file for writing! Ensure FFmpeg is installed and configured." << std::endl;
        return -1;
    }

    // Generate video frames with numbers
    for (int i = 0; i < duration; ++i) {
        // Create a black image as the frame
        cv::Mat frame(frameHeight, frameWidth, CV_8UC3, cv::Scalar(0, 0, 0));

        // Draw the number on the frame
        std::string text = std::to_string(i);
        int fontFace = cv::FONT_HERSHEY_SIMPLEX;
        double fontScale = 4.0;
        int thickness = 3;
        cv::Size textSize = cv::getTextSize(text, fontFace, fontScale, thickness, nullptr);
        cv::Point textOrg((frameWidth - textSize.width) / 2, (frameHeight + textSize.height) / 2);

        cv::putText(frame, text, textOrg, fontFace, fontScale, cv::Scalar(0, 255, 0), thickness);

        // Write the frame to the video
        videoWriter.write(frame);
    }

    // Release the VideoWriter object
    videoWriter.release();
    std::cout << "Video has been saved as " << videoFileName << std::endl;

    // Read and play the video
    cv::VideoCapture videoReader(videoFileName);
    if (!videoReader.isOpened()) {
        std::cerr << "Failed to open the video file for reading! Ensure FFmpeg is installed and configured." << std::endl;
        return -1;
    }

    cv::Mat frame;
    while (true) {
        videoReader >> frame; // Read a frame from the video
        if (frame.empty()) break; // If the frame is empty, the video has ended

        cv::imshow("Video Playback", frame); // Display the frame
        if (cv::waitKey(1000 / fps) == 27) break; // Exit playback if the ESC key is pressed
    }

    videoReader.release();
    cv::destroyAllWindows();
    return 0;
}