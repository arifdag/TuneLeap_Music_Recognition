import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:provider/provider.dart';
import 'package:just_audio/just_audio.dart';
import 'dart:async';
import 'dart:io';
import 'dart:math';
import '../widgets/recognition_result_sheet.dart';
import '../widgets/audio_settings_sheet.dart';
import '../providers/settings_provider.dart';
import '../services/audio_recording_service.dart';
import '../services/recognition_service.dart';

class RecognitionScreen extends StatefulWidget {
  final Animation<double> pulseAnimation;

  RecognitionScreen({required this.pulseAnimation});

  @override
  _RecognitionScreenState createState() => _RecognitionScreenState();
}

class _RecognitionScreenState extends State<RecognitionScreen> with TickerProviderStateMixin {
  bool _isRecording = false;
  bool _isProcessing = false;
  double _recordingLevel = 0.0;
  Timer? _recordingTimer;
  int _recordingSeconds = 0;
  String _status = "Tap to start recognition";
  File? _currentRecordingFile;

  late AnimationController _waveController;
  late Animation<double> _waveAnimation;
  
  // Add controllers for new animations
  late AnimationController _pulseController;
  late AnimationController _colorController;
  late Animation<Color?> _colorAnimation;
  
  final AudioRecordingService _audioService = AudioRecordingService();
  final RecognitionService _recognitionService = RecognitionService();
  final AudioPlayer _audioPlayer = AudioPlayer();

  // List of colors for dynamic animation
  final List<Color> _visualizerColors = [
    Colors.purple,
    Colors.deepPurple,
    Colors.indigo,
    Colors.blue,
    Colors.teal,
    Colors.cyan,
  ];

  @override
  void initState() {
    super.initState();
    _waveController = AnimationController(
      duration: Duration(milliseconds: 800),
      vsync: this,
    )..repeat();
    _waveAnimation = Tween<double>(begin: 0, end: 1).animate(_waveController);
    
    // Initialize new animation controllers
    _pulseController = AnimationController(
      duration: Duration(milliseconds: 1500),
      vsync: this,
    )..repeat(reverse: true);
    
    _colorController = AnimationController(
      duration: Duration(seconds: 3),
      vsync: this,
    )..repeat();
    
    _colorAnimation = ColorTween(
      begin: Colors.purple.shade400,
      end: Colors.blue.shade400,
    ).animate(CurvedAnimation(
      parent: _colorController,
      curve: Curves.easeInOut,
    ));
  }

  @override
  void dispose() {
    _recordingTimer?.cancel();
    _waveController.dispose();
    _pulseController.dispose();
    _colorController.dispose();
    _audioService.dispose();
    _audioPlayer.dispose();
    super.dispose();
  }

  void _toggleRecording() {
    if (_isRecording) {
      _stopRecording();
    } else {
      _startRecording();
    }
  }

  void _startRecording() async {
    final settingsProvider = context.read<SettingsProvider>();
    
    // Show recording settings for debugging
    print('Starting recording with settings:');
    print('- Sample Rate: ${settingsProvider.getSampleRate()}');
    print('- Audio Quality: ${settingsProvider.audioQuality}');
    print('- Noise Reduction: ${settingsProvider.noiseReduction}');
    
    // Request permissions and start recording
    final recordingFile = await _audioService.startRecording(
      sampleRate: settingsProvider.getSampleRate(),
    );
    
    if (recordingFile == null) {
      setState(() {
        _status = "Failed to start recording. Check permissions.";
      });
      
      // Show more detailed error dialog
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: Text('Recording Failed'),
          content: Text(
            'Could not start recording. Please ensure:\n\n'
            '1. Microphone permission is granted\n'
            '2. No other app is using the microphone\n'
            '3. Your device supports audio recording\n\n'
            'Try closing other apps and restarting the app.'
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text('OK'),
            ),
            TextButton(
              onPressed: () {
                Navigator.pop(context);
                _audioService.checkAndRequestPermissions();
              },
              child: Text('Check Permissions'),
            ),
          ],
        ),
      );
      return;
    }

    setState(() {
      _isRecording = true;
      _recordingSeconds = 0;
      _status = "Listening...";
      _currentRecordingFile = recordingFile;
    });

    // Start recording timer and amplitude monitoring
    _recordingTimer = Timer.periodic(Duration(milliseconds: 100), (timer) async {
      try {
        // Get amplitude from recorder every 100ms for more responsive animation
        final amplitude = await _audioService.recorder.getAmplitude();
        double normalizedLevel = amplitude.current / 100; // Normalize between 0-1
        
        // Clamp between 0.2 and 1.0 to ensure some movement
        normalizedLevel = normalizedLevel.clamp(0.2, 1.0);
        
        setState(() {
          _recordingLevel = normalizedLevel;
          
          // Only increment seconds counter every 10 ticks (every second)
          if (timer.tick % 10 == 0) {
            _recordingSeconds++;
          }
        });
        
        // Auto-stop at configured duration
        if (_recordingSeconds >= settingsProvider.recordingDuration) {
          _stopRecording();
        }
      } catch (e) {
        print('Error getting amplitude: $e');
      }
    });

    HapticFeedback.lightImpact();
  }

  void _stopRecording() async {
    _recordingTimer?.cancel();
    
    final path = await _audioService.stopRecording();
    
    if (path == null) {
      setState(() {
        _isRecording = false;
        _status = "Recording failed. Try again.";
      });
      return;
    }

    setState(() {
      _isRecording = false;
      _isProcessing = true;
      _status = "Processing audio...";
    });

    _processAudio();
    HapticFeedback.mediumImpact();
  }

  void _processAudio() async {
    if (_currentRecordingFile == null) {
      setState(() {
        _isProcessing = false;
        _status = "No recording to process";
      });
      return;
    }

    try {
      // Send audio to recognition API
      final result = await _recognitionService.recognizeAudio(_currentRecordingFile!);
      
      if (result['status'] == 'accepted' && result['task_id'] != null) {
        // Poll for recognition result
        setState(() {
          _status = "Analyzing audio...";
        });
        
        final recognitionResult = await _recognitionService.pollForResult(
          result['task_id'],
          timeout: Duration(seconds: 30),
          context: context, // Pass context for login prompt
        );
        
        if (recognitionResult['status'] == 'success' && recognitionResult['results'] != null) {
          _showRecognitionResult(recognitionResult['results']);
        } else if (recognitionResult['status'] == 'no_match') {
          setState(() {
            _isProcessing = false;
            _status = "No match found. Try again!";
          });
          
          Timer(Duration(seconds: 2), () {
            if (mounted) {
              setState(() {
                _status = "Tap to start recognition";
              });
            }
          });
        } else {
          setState(() {
            _isProcessing = false;
            _status = recognitionResult['message'] ?? "Recognition failed";
          });
          
          Timer(Duration(seconds: 2), () {
            if (mounted) {
              setState(() {
                _status = "Tap to start recognition";
              });
            }
          });
        }
      } else {
        setState(() {
          _isProcessing = false;
          _status = result['message'] ?? "Failed to start recognition";
        });
      }
    } catch (e) {
      setState(() {
        _isProcessing = false;
        _status = "Error: Check your connection";
      });
      
      Timer(Duration(seconds: 2), () {
        if (mounted) {
          setState(() {
            _status = "Tap to start recognition";
          });
        }
      });
    } finally {
      // Keep the recording file for later playback - don't delete it
      print('Recording saved: ${_currentRecordingFile?.path}');
      _currentRecordingFile = null;
    }
  }

  void _showRecognitionResult(List<dynamic> results) {
    setState(() {
      _isProcessing = false;
      _status = "Match found!";
    });

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => RecognitionResultSheet(results: results),
    );

    Timer(Duration(seconds: 1), () {
      if (mounted) {
        setState(() {
          _status = "Tap to start recognition";
        });
      }
    });
  }

  @override
  Widget build(BuildContext context) {
    final settingsProvider = context.watch<SettingsProvider>();
    
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: Text('Music Recognition', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0,
        actions: [
          IconButton(
            icon: Icon(Icons.folder_outlined),
            onPressed: () => _showRecordingsBottomSheet(),
            tooltip: 'View Recordings',
          ),
          IconButton(
            icon: Icon(Icons.tune),
            onPressed: () => _showAudioSettings(),
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                // Enhanced Recording Animation
                AnimatedBuilder(
                  animation: Listenable.merge([widget.pulseAnimation, _colorAnimation, _pulseController]),
                  builder: (context, child) {
                    return Stack(
                      alignment: Alignment.center,
                      children: [
                        // Outer glow circles
                        if (_isRecording)
                          ...List.generate(3, (index) {
                            final delay = index * 0.3;
                            final scale = 1.0 + (_pulseController.value * (0.3 + (delay * 0.2)));
                            final opacity = (1.0 - _pulseController.value) * 0.3;
                            return Transform.scale(
                              scale: scale,
                              child: Container(
                                width: 200,
                                height: 200,
                                decoration: BoxDecoration(
                                  shape: BoxShape.circle,
                                  color: _colorAnimation.value!.withOpacity(opacity),
                                ),
                              ),
                            );
                          }),
                        
                        // Main button
                        Transform.scale(
                          scale: _isRecording 
                              ? 1.0 + (_recordingLevel * 0.15) 
                              : widget.pulseAnimation.value,
                          child: Container(
                            width: 200,
                            height: 200,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              gradient: LinearGradient(
                                colors: _isRecording
                                    ? [_colorAnimation.value!.withOpacity(0.8), _colorAnimation.value!]
                                    : [Colors.purple.shade400, Colors.purple.shade600],
                                begin: Alignment.topLeft,
                                end: Alignment.bottomRight,
                              ),
                              boxShadow: [
                                BoxShadow(
                                  color: (_isRecording ? _colorAnimation.value! : Colors.purple).withOpacity(0.3),
                                  blurRadius: 20,
                                  spreadRadius: 5,
                                ),
                              ],
                            ),
                            child: Material(
                              color: Colors.transparent,
                              child: InkWell(
                                borderRadius: BorderRadius.circular(100),
                                onTap: _isProcessing ? null : _toggleRecording,
                                child: Center(
                                  child: _isProcessing
                                      ? CircularProgressIndicator(color: Colors.white, strokeWidth: 3)
                                      : Icon(
                                    _isRecording ? Icons.stop : Icons.mic,
                                    size: 80,
                                    color: Colors.white,
                                  ),
                                ),
                              ),
                            ),
                          ),
                        ),
                      ],
                    );
                  },
                ),
                SizedBox(height: 40),

                // Status Text
                Text(
                  _status,
                  style: TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w500,
                    color: Colors.grey[700],
                  ),
                ),

                if (_isRecording) ...[
                  SizedBox(height: 20),
                  Text(
                    '${_recordingSeconds}s / ${settingsProvider.recordingDuration}s',
                    style: TextStyle(
                      fontSize: 24,
                      fontWeight: FontWeight.bold,
                      color: Colors.red,
                    ),
                  ),
                  SizedBox(height: 20),
                  // Audio Level Visualization
                  _buildAudioLevelIndicator(),
                ],
              ],
            ),
          ),

          // Quick Settings
          Container(
            padding: EdgeInsets.all(20),
            child: Card(
              child: Padding(
                padding: EdgeInsets.all(16),
                child: Column(
                  children: [
                    Row(
                      children: [
                        Icon(Icons.noise_control_off, color: Colors.purple),
                        SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            'Noise Reduction',
                            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
                          ),
                        ),
                        Switch(
                          value: settingsProvider.noiseReduction,
                          onChanged: (value) {
                            settingsProvider.setNoiseReduction(value);
                          },
                          activeColor: Colors.purple,
                        ),
                      ],
                    ),
                    Divider(),
                    // Test Recording Button
                    TextButton.icon(
                      icon: Icon(Icons.mic_external_on),
                      label: Text('Test Microphone (3s recording)'),
                      onPressed: _isRecording || _isProcessing ? null : _testMicrophone,
                      style: TextButton.styleFrom(
                        foregroundColor: Colors.purple,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildAudioLevelIndicator() {
    return AnimatedBuilder(
      animation: _waveAnimation,
      builder: (context, child) {
        return Container(
          height: 60,
          width: 200,
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: List.generate(15, (index) {
              // Create more interesting wave patterns with multiple sine waves
              final double wave1 = sin((_waveAnimation.value * 2 * pi) + (index * 0.2)) * 0.5;
              final double wave2 = sin((_waveAnimation.value * 4 * pi) + (index * 0.4)) * 0.3;
              final double wave3 = sin((_waveAnimation.value * 8 * pi) + (index * 0.6)) * 0.2;
              
              // Combine waves and apply recording level
              double height = (wave1 + wave2 + wave3) * _recordingLevel * 45;
              
              // Ensure minimum height
              height = 5 + height.abs();
              
              // Add a small random variation for more natural look
              final random = index % 3 == 0 ? (Random().nextDouble() * 5 * _recordingLevel) : 0;
              height += random;
              
              // Dynamic color based on position and recording level
              final Color barColor = _visualizerColors[
                (index + (_recordingLevel * 10).toInt()) % _visualizerColors.length
              ];
              
              return Container(
                margin: EdgeInsets.symmetric(horizontal: 1),
                width: 4,
                height: height,
                decoration: BoxDecoration(
                  color: barColor,
                  borderRadius: BorderRadius.circular(2),
                  boxShadow: [
                    BoxShadow(
                      color: barColor.withOpacity(0.5),
                      blurRadius: 3,
                      spreadRadius: 1,
                    ),
                  ],
                ),
              );
            }),
          ),
        );
      },
    );
  }

  void _showAudioSettings() {
    showModalBottomSheet(
      context: context,
      builder: (context) => AudioSettingsSheet(),
    );
  }

  void _showRecordingsBottomSheet() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => DraggableScrollableSheet(
        initialChildSize: 0.7,
        maxChildSize: 0.9,
        minChildSize: 0.5,
        builder: (context, scrollController) {
          return Container(
            decoration: BoxDecoration(
              color: Colors.white,
              borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
            ),
            child: Column(
              children: [
                Container(
                  padding: EdgeInsets.all(16),
                  child: Row(
                    children: [
                      Text(
                        'Saved Recordings',
                        style: TextStyle(
                          fontSize: 20,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                      Spacer(),
                      TextButton(
                        onPressed: () => _clearAllRecordings(),
                        child: Text('Clear All', style: TextStyle(color: Colors.red)),
                      ),
                    ],
                  ),
                ),
                Expanded(
                  child: FutureBuilder<List<File>>(
                    future: _audioService.getSavedRecordings(),
                    builder: (context, snapshot) {
                      if (snapshot.connectionState == ConnectionState.waiting) {
                        return Center(child: CircularProgressIndicator());
                      }
                      
                      if (!snapshot.hasData || snapshot.data!.isEmpty) {
                        return Center(
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              Icon(Icons.mic_off, size: 64, color: Colors.grey),
                              SizedBox(height: 16),
                              Text(
                                'No recordings yet',
                                style: TextStyle(
                                  fontSize: 18,
                                  color: Colors.grey[600],
                                ),
                              ),
                              Text(
                                'Record some audio to see it here',
                                style: TextStyle(
                                  fontSize: 14,
                                  color: Colors.grey[500],
                                ),
                              ),
                            ],
                          ),
                        );
                      }
                      
                      final recordings = snapshot.data!;
                      return ListView.builder(
                        controller: scrollController,
                        itemCount: recordings.length,
                        itemBuilder: (context, index) {
                          final recording = recordings[index];
                          final fileName = recording.path.split('/').last;
                          final fileSize = recording.lengthSync();
                          final fileSizeKB = (fileSize / 1024).toStringAsFixed(1);
                          final dateModified = recording.lastModifiedSync();
                          
                          return Card(
                            margin: EdgeInsets.symmetric(horizontal: 16, vertical: 4),
                            child: ListTile(
                              leading: CircleAvatar(
                                backgroundColor: Colors.purple[100],
                                child: Icon(Icons.audiotrack, color: Colors.purple),
                              ),
                              title: Text(fileName),
                              subtitle: Text(
                                '${fileSizeKB}KB • ${_formatDateTime(dateModified)}',
                                style: TextStyle(fontSize: 12),
                              ),
                              trailing: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  IconButton(
                                    icon: Icon(Icons.play_arrow, color: Colors.green),
                                    onPressed: () => _playRecording(recording),
                                  ),
                                  IconButton(
                                    icon: Icon(Icons.delete, color: Colors.red),
                                    onPressed: () => _deleteRecording(recording),
                                  ),
                                ],
                              ),
                            ),
                          );
                        },
                      );
                    },
                  ),
                ),
              ],
            ),
          );
        },
      ),
    );
  }

  String _formatDateTime(DateTime dateTime) {
    return '${dateTime.day}/${dateTime.month}/${dateTime.year} ${dateTime.hour}:${dateTime.minute.toString().padLeft(2, '0')}';
  }

  void _playRecording(File recording) async {
    try {
      // Stop any currently playing audio
      await _audioPlayer.stop();
      
      // Set the audio source to the recording file
      await _audioPlayer.setFilePath(recording.path);
      
      // Show playing status
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Row(
            children: [
              Icon(Icons.play_arrow, color: Colors.white),
              SizedBox(width: 8),
              Expanded(child: Text('Playing: ${recording.path.split('/').last}')),
            ],
          ),
          duration: Duration(seconds: 2),
          action: SnackBarAction(
            label: 'Stop',
            onPressed: () => _audioPlayer.stop(),
          ),
        ),
      );
      
      // Play the audio
      await _audioPlayer.play();
      
    } catch (e) {
      print('Error playing recording: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('Error playing recording: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  void _deleteRecording(File recording) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Delete Recording'),
        content: Text('Are you sure you want to delete this recording?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              final success = await _audioService.deleteRecording(recording);
              if (success) {
                ScaffoldMessenger.of(context).showSnackBar(
                  SnackBar(content: Text('Recording deleted')),
                );
                // Refresh the bottom sheet
                Navigator.pop(context);
                _showRecordingsBottomSheet();
              }
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: Text('Delete'),
          ),
        ],
      ),
    );
  }

  void _clearAllRecordings() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Clear All Recordings'),
        content: Text('Are you sure you want to delete all recordings? This action cannot be undone.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () async {
              Navigator.pop(context);
              await _audioService.clearAllRecordings();
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('All recordings cleared')),
              );
              // Refresh the bottom sheet
              Navigator.pop(context);
              _showRecordingsBottomSheet();
            },
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: Text('Clear All'),
          ),
        ],
      ),
    );
  }

  void _testMicrophone() async {
    setState(() {
      _status = "Testing microphone...";
    });

    // Start a test recording with fixed settings
    final testFile = await _audioService.startRecording(sampleRate: 16000);
    
    if (testFile == null) {
      setState(() {
        _status = "Microphone test failed";
      });
      return;
    }

    // Record for 3 seconds
    await Future.delayed(Duration(seconds: 3));
    
    final path = await _audioService.stopRecording();
    
    if (path != null) {
      final file = File(path);
      final fileSize = await file.length();
      
      setState(() {
        _status = "Test complete";
      });
      
      // Show test results
      showDialog(
        context: context,
        builder: (context) => AlertDialog(
          title: Text('Microphone Test Results'),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text('Recording saved successfully!'),
              SizedBox(height: 8),
              Text('File size: ${(fileSize / 1024).toStringAsFixed(1)} KB'),
              Text('Sample rate: 16000 Hz'),
              Text('Duration: 3 seconds'),
              SizedBox(height: 16),
              Text(
                fileSize < 10000 
                  ? '⚠️ File seems small. There might be an issue with the microphone.' 
                  : '✅ File size looks normal.',
                style: TextStyle(
                  color: fileSize < 10000 ? Colors.orange : Colors.green,
                  fontWeight: FontWeight.bold,
                ),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(context),
              child: Text('Close'),
            ),
            ElevatedButton.icon(
              icon: Icon(Icons.play_arrow),
              label: Text('Play Test'),
              onPressed: () {
                Navigator.pop(context);
                _playRecording(file);
              },
            ),
          ],
        ),
      );
    } else {
      setState(() {
        _status = "Test failed";
      });
    }
  }
} 