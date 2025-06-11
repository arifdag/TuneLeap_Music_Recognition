import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_service.dart';
import '../providers/settings_provider.dart';
import 'login_screen.dart';

class SettingsScreen extends StatefulWidget {
  @override
  _SettingsScreenState createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  final AuthService _authService = AuthService();

  @override
  Widget build(BuildContext context) {
    final settingsProvider = context.watch<SettingsProvider>();
    
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: Text('Settings', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0,
      ),
      body: ListView(
        children: [
          _buildSectionHeader('Audio Processing'),
          _buildSwitchTile(
            'Noise Reduction',
            'Reduce background noise during recognition',
            settingsProvider.noiseReduction,
            (value) => settingsProvider.setNoiseReduction(value),
          ),
          _buildListTile(
            'Audio Quality',
            settingsProvider.audioQuality,
            Icons.high_quality,
            () => _showAudioQualityDialog(settingsProvider),
          ),
          _buildSliderTile(
            'Recording Duration',
            'Maximum recording time: ${settingsProvider.recordingDuration}s',
            settingsProvider.recordingDuration.toDouble(),
            5,
            30,
            (value) => settingsProvider.setRecordingDuration(value.round()),
          ),

          _buildSectionHeader('Playback'),
          _buildSwitchTile(
            'Auto-play Results',
            'Automatically play recognized songs',
            settingsProvider.autoPlay,
            (value) => settingsProvider.setAutoPlay(value),
          ),

          _buildSectionHeader('Notifications'),
          _buildSwitchTile(
            'Recognition Notifications',
            'Get notified about successful recognitions',
            settingsProvider.notifications,
            (value) => settingsProvider.setNotifications(value),
          ),

          _buildSectionHeader('Data & Privacy'),
          _buildListTile(
            'Clear History',
            'Remove all recognition history',
            Icons.delete_sweep,
            () => _showClearDataDialog(),
          ),
          _buildListTile(
            'Export Data',
            'Export your recognition history',
            Icons.file_download,
            () {},
          ),

          _buildSectionHeader('Account'),
          _buildListTile(
            'Logout',
            'Sign out of your account',
            Icons.logout,
            () => _showLogoutDialog(),
          ),

          _buildSectionHeader('About'),
          _buildListTile(
            'App Version',
            '1.0.0',
            Icons.info_outline,
            () {},
          ),
          _buildListTile(
            'Privacy Policy',
            'View privacy policy',
            Icons.privacy_tip,
            () {},
          ),
          _buildListTile(
            'Terms of Service',
            'View terms of service',
            Icons.description,
            () {},
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Container(
      padding: EdgeInsets.fromLTRB(16, 24, 16, 8),
      child: Text(
        title,
        style: TextStyle(
          fontSize: 14,
          fontWeight: FontWeight.bold,
          color: Colors.purple,
        ),
      ),
    );
  }

  Widget _buildSwitchTile(String title, String subtitle, bool value, Function(bool) onChanged) {
    return Card(
      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 2),
      child: SwitchListTile(
        title: Text(title),
        subtitle: Text(subtitle),
        value: value,
        onChanged: onChanged,
        activeColor: Colors.purple,
      ),
    );
  }

  Widget _buildListTile(String title, String subtitle, IconData icon, VoidCallback onTap) {
    return Card(
      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 2),
      child: ListTile(
        leading: Icon(icon, color: Colors.purple),
        title: Text(title),
        subtitle: Text(subtitle),
        trailing: Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }

  Widget _buildSliderTile(String title, String subtitle, double value, double min, double max, Function(double) onChanged) {
    return Card(
      margin: EdgeInsets.symmetric(horizontal: 16, vertical: 2),
      child: Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title, style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500)),
            Text(subtitle, style: TextStyle(color: Colors.grey[600])),
            Slider(
              value: value,
              min: min,
              max: max,
              divisions: (max - min).round(),
              onChanged: onChanged,
              activeColor: Colors.purple,
            ),
          ],
        ),
      ),
    );
  }

  void _showAudioQualityDialog(SettingsProvider settingsProvider) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Audio Quality'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            RadioListTile<String>(
              title: Text('Low (16kHz)'),
              value: 'Low',
              groupValue: settingsProvider.audioQuality,
              onChanged: (value) {
                settingsProvider.setAudioQuality(value!);
                Navigator.pop(context);
              },
            ),
            RadioListTile<String>(
              title: Text('Medium (22kHz)'),
              value: 'Medium',
              groupValue: settingsProvider.audioQuality,
              onChanged: (value) {
                settingsProvider.setAudioQuality(value!);
                Navigator.pop(context);
              },
            ),
            RadioListTile<String>(
              title: Text('High (44kHz)'),
              value: 'High',
              groupValue: settingsProvider.audioQuality,
              onChanged: (value) {
                settingsProvider.setAudioQuality(value!);
                Navigator.pop(context);
              },
            ),
          ],
        ),
      ),
    );
  }

  void _showClearDataDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Clear All Data'),
        content: Text('This will permanently delete all your recognition history, playlists, and preferences. This action cannot be undone.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: Text('Clear All'),
          ),
        ],
      ),
    );
  }

  void _showLogoutDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Logout'),
        content: Text('Are you sure you want to sign out?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => _performLogout(),
            style: ElevatedButton.styleFrom(backgroundColor: Colors.red),
            child: Text('Logout'),
          ),
        ],
      ),
    );
  }

  void _performLogout() async {
    // Close the dialog
    Navigator.pop(context);
    
    // Show loading indicator
    showDialog(
      context: context,
      barrierDismissible: false,
      builder: (context) => Center(
        child: CircularProgressIndicator(),
      ),
    );
    
    // Perform logout
    await _authService.logout();
    
    // Navigate to login screen and remove all previous routes
    Navigator.of(context).pushAndRemoveUntil(
      MaterialPageRoute(builder: (context) => LoginScreen()),
      (Route<dynamic> route) => false,
    );
  }
} 