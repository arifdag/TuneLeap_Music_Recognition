import 'package:flutter/material.dart';

class AudioSettingsSheet extends StatefulWidget {
  @override
  _AudioSettingsSheetState createState() => _AudioSettingsSheetState();
}

class _AudioSettingsSheetState extends State<AudioSettingsSheet> {
  int _sampleRate = 44100;
  int _bitDepth = 16;
  int _channels = 1;
  bool _autoGainControl = true;
  bool _echoCancellation = true;
  double _sensitivity = 0.5;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      child: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Center(
              child: Container(
                width: 40,
                height: 4,
                decoration: BoxDecoration(
                  color: Colors.grey[300],
                  borderRadius: BorderRadius.circular(2),
                ),
              ),
            ),
            SizedBox(height: 20),

            Text(
              'Audio Settings',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.bold,
              ),
            ),
            SizedBox(height: 20),

            // Sample Rate
            Text(
              'Sample Rate',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
            ),
            SizedBox(height: 8),
            DropdownButtonFormField<int>(
              value: _sampleRate,
              decoration: InputDecoration(
                border: OutlineInputBorder(),
                contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              ),
              items: [8000, 16000, 22050, 44100, 48000].map((rate) {
                return DropdownMenuItem(
                  value: rate,
                  child: Text('${rate} Hz'),
                );
              }).toList(),
              onChanged: (value) => setState(() => _sampleRate = value!),
            ),
            SizedBox(height: 16),

            // Bit Depth
            Text(
              'Bit Depth',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
            ),
            SizedBox(height: 8),
            DropdownButtonFormField<int>(
              value: _bitDepth,
              decoration: InputDecoration(
                border: OutlineInputBorder(),
                contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              ),
              items: [16, 24, 32].map((depth) {
                return DropdownMenuItem(
                  value: depth,
                  child: Text('${depth} bit'),
                );
              }).toList(),
              onChanged: (value) => setState(() => _bitDepth = value!),
            ),
            SizedBox(height: 16),

            // Channels
            Text(
              'Channels',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
            ),
            SizedBox(height: 8),
            DropdownButtonFormField<int>(
              value: _channels,
              decoration: InputDecoration(
                border: OutlineInputBorder(),
                contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              ),
              items: [
                DropdownMenuItem(value: 1, child: Text('Mono')),
                DropdownMenuItem(value: 2, child: Text('Stereo')),
              ],
              onChanged: (value) => setState(() => _channels = value!),
            ),
            SizedBox(height: 20),

            // Audio Processing Options
            SwitchListTile(
              title: Text('Auto Gain Control'),
              subtitle: Text('Automatically adjust recording volume'),
              value: _autoGainControl,
              onChanged: (value) => setState(() => _autoGainControl = value),
              activeColor: Colors.purple,
              contentPadding: EdgeInsets.zero,
            ),

            SwitchListTile(
              title: Text('Echo Cancellation'),
              subtitle: Text('Reduce echo and feedback'),
              value: _echoCancellation,
              onChanged: (value) => setState(() => _echoCancellation = value),
              activeColor: Colors.purple,
              contentPadding: EdgeInsets.zero,
            ),

            SizedBox(height: 16),

            // Sensitivity Slider
            Text(
              'Microphone Sensitivity',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
            ),
            Slider(
              value: _sensitivity,
              onChanged: (value) => setState(() => _sensitivity = value),
              activeColor: Colors.purple,
              divisions: 10,
              label: '${(_sensitivity * 100).round()}%',
            ),

            SizedBox(height: 20),

            // Apply Button
            SizedBox(
              width: double.infinity,
              child: ElevatedButton(
                onPressed: () {
                  Navigator.pop(context);
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Audio settings applied'),
                      backgroundColor: Colors.purple,
                    ),
                  );
                },
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.purple,
                  foregroundColor: Colors.white,
                  padding: EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
                child: Text(
                  'Apply Settings',
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}


