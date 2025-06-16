import 'dart:io';
import 'package:record/record.dart';
import 'package:path_provider/path_provider.dart';
import 'package:permission_handler/permission_handler.dart';

class AudioRecordingService {
  final AudioRecorder _recorder = AudioRecorder();
  
  // Expose the recorder to access amplitude data
  AudioRecorder get recorder => _recorder;
  
  Future<bool> checkAndRequestPermissions() async {
    // Check microphone permission
    var micStatus = await Permission.microphone.status;
    
    if (!micStatus.isGranted) {
      micStatus = await Permission.microphone.request();
    }
    
    // On Android, also check for storage permissions
    if (Platform.isAndroid) {
      var storageStatus = await Permission.storage.status;
      if (!storageStatus.isGranted) {
        await Permission.storage.request();
      }
    }
    
    return micStatus.isGranted;
  }
  
  Future<bool> isRecording() async {
    return await _recorder.isRecording();
  }
  
  Future<File?> startRecording({int sampleRate = 44100, bool useAAC = false}) async {
    try {
      // Check permissions
      final hasPermission = await checkAndRequestPermissions();
      if (!hasPermission) {
        throw Exception('Microphone permission denied');
      }
      
      // Check if recording is supported
      if (!await _recorder.hasPermission()) {
        throw Exception('Recording not supported on this device');
      }
      
      // Get documents directory for persistent storage
      final dir = await getApplicationDocumentsDirectory();
      final recordingsDir = Directory('${dir.path}/recordings');
      
      // Create recordings directory if it doesn't exist
      if (!await recordingsDir.exists()) {
        await recordingsDir.create(recursive: true);
      }
      
      final timestamp = DateTime.now().millisecondsSinceEpoch;
      final formattedDate = DateTime.now().toIso8601String().replaceAll(':', '-').replaceAll('.', '-');
      final extension = useAAC ? 'm4a' : 'wav';
      final path = '${recordingsDir.path}/recording_$formattedDate.$extension';
      
      // Configure recording settings with proper configuration
      RecordConfig config;
      
      if (Platform.isAndroid) {
        // Android-specific configuration
        config = RecordConfig(
          encoder: useAAC ? AudioEncoder.aacLc : AudioEncoder.wav,
          sampleRate: sampleRate,
          bitRate: useAAC ? 128000 : 256000,
          numChannels: 1,
          androidConfig: AndroidRecordConfig(
            audioSource: AndroidAudioSource.mic,
            useLegacy: false,
          ),
        );
      } else if (Platform.isIOS) {
        // iOS-specific configuration
        config = RecordConfig(
          encoder: useAAC ? AudioEncoder.aacLc : AudioEncoder.wav,
          sampleRate: sampleRate,
          bitRate: useAAC ? 128000 : 256000,
          numChannels: 1,
          // iOS config doesn't need special settings, uses defaults
        );
      } else {
        // Default configuration for other platforms
        config = RecordConfig(
          encoder: useAAC ? AudioEncoder.aacLc : AudioEncoder.wav,
          sampleRate: sampleRate,
          bitRate: useAAC ? 128000 : 256000,
          numChannels: 1,
        );
      }
      
      // Start recording
      await _recorder.start(config, path: path);
      
      print('Recording started: $path');
      print('Sample rate: $sampleRate, Encoder: ${useAAC ? "AAC" : "WAV"}');
      return File(path);
    } catch (e) {
      print('Error starting recording: $e');
      return null;
    }
  }
  
  Future<String?> stopRecording() async {
    try {
      final path = await _recorder.stop();
      print('Recording stopped: $path');
      
      // Verify the file exists and has content
      if (path != null) {
        final file = File(path);
        if (await file.exists()) {
          final fileSize = await file.length();
          print('Recording file size: ${fileSize} bytes');
          if (fileSize < 1000) { // Less than 1KB might indicate empty/corrupt file
            print('Warning: Recording file seems too small, might be corrupted');
          }
        }
      }
      
      return path;
    } catch (e) {
      print('Error stopping recording: $e');
      return null;
    }
  }
  
  // Get all saved recordings
  Future<List<File>> getSavedRecordings() async {
    try {
      final dir = await getApplicationDocumentsDirectory();
      final recordingsDir = Directory('${dir.path}/recordings');
      
      if (!await recordingsDir.exists()) {
        return [];
      }
      
      final files = recordingsDir
          .listSync()
          .where((file) => file.path.endsWith('.wav') || file.path.endsWith('.m4a'))
          .map((file) => File(file.path))
          .toList();
      
      // Sort by modification date (newest first)
      files.sort((a, b) => b.lastModifiedSync().compareTo(a.lastModifiedSync()));
      
      return files;
    } catch (e) {
      print('Error getting saved recordings: $e');
      return [];
    }
  }
  
  // Delete a specific recording
  Future<bool> deleteRecording(File file) async {
    try {
      if (await file.exists()) {
        await file.delete();
        return true;
      }
      return false;
    } catch (e) {
      print('Error deleting recording: $e');
      return false;
    }
  }
  
  // Clear all recordings
  Future<void> clearAllRecordings() async {
    try {
      final recordings = await getSavedRecordings();
      for (final recording in recordings) {
        await deleteRecording(recording);
      }
    } catch (e) {
      print('Error clearing recordings: $e');
    }
  }
  
  void dispose() {
    _recorder.dispose();
  }
} 