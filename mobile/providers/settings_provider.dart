import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';

class SettingsProvider extends ChangeNotifier {
  late SharedPreferences _prefs;
  
  // Default settings
  bool _noiseReduction = true;
  bool _autoPlay = false;
  bool _notifications = true;
  String _audioQuality = 'High';
  int _recordingDuration = 10;
  String _encoderFormat = 'WAV';


  bool get noiseReduction => _noiseReduction;
  bool get autoPlay => _autoPlay;
  bool get notifications => _notifications;
  String get audioQuality => _audioQuality;
  int get recordingDuration => _recordingDuration;
  String get encoderFormat => _encoderFormat;

  // Initialize settings from SharedPreferences
  Future<void> init() async {
    _prefs = await SharedPreferences.getInstance();
    _loadSettings();
  }

  void _loadSettings() {
    _noiseReduction = _prefs.getBool('noiseReduction') ?? true;
    _autoPlay = _prefs.getBool('autoPlay') ?? false;
    _notifications = _prefs.getBool('notifications') ?? true;
    _audioQuality = _prefs.getString('audioQuality') ?? 'High';
    _recordingDuration = _prefs.getInt('recordingDuration') ?? 10;
    _encoderFormat = _prefs.getString('encoderFormat') ?? 'WAV';
    notifyListeners();
  }

  // Setters with persistence
  Future<void> setNoiseReduction(bool value) async {
    _noiseReduction = value;
    await _prefs.setBool('noiseReduction', value);
    notifyListeners();
  }

  Future<void> setAutoPlay(bool value) async {
    _autoPlay = value;
    await _prefs.setBool('autoPlay', value);
    notifyListeners();
  }

  Future<void> setNotifications(bool value) async {
    _notifications = value;
    await _prefs.setBool('notifications', value);
    notifyListeners();
  }

  Future<void> setAudioQuality(String value) async {
    _audioQuality = value;
    await _prefs.setString('audioQuality', value);
    notifyListeners();
  }

  Future<void> setRecordingDuration(int value) async {
    _recordingDuration = value;
    await _prefs.setInt('recordingDuration', value);
    notifyListeners();
  }

  Future<void> setEncoderFormat(String value) async {
    _encoderFormat = value;
    await _prefs.setString('encoderFormat', value);
    notifyListeners();
  }

  // Get audio sample rate based on quality
  int getSampleRate() {
    switch (_audioQuality) {
      case 'Low':
        return 16000;
      case 'Medium':
        return 22050;
      case 'High':
      default:
        return 44100;
    }
  }
} 