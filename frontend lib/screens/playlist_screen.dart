import 'package:flutter/material.dart';

class PlaylistScreen extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.grey[50],
      appBar: AppBar(
        title: Text('Playlists', style: TextStyle(fontWeight: FontWeight.bold)),
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
        elevation: 0,
        actions: [
          IconButton(
            icon: Icon(Icons.add),
            onPressed: () => _showCreatePlaylistDialog(context),
          ),
        ],
      ),
      body: ListView(
        padding: EdgeInsets.all(16),
        children: [
          _buildPlaylistCard(
            'Auto-Generated',
            'Songs similar to your recent recognitions',
            25,
            Colors.purple,
            Icons.auto_awesome,
          ),
          _buildPlaylistCard(
            'Favorites',
            'Your liked songs',
            12,
            Colors.red,
            Icons.favorite,
          ),
          _buildPlaylistCard(
            'Recently Recognized',
            'Your latest discoveries',
            8,
            Colors.blue,
            Icons.history,
          ),
          _buildPlaylistCard(
            'Pop Hits',
            'Popular songs you\'ve discovered',
            15,
            Colors.green,
            Icons.trending_up,
          ),
        ],
      ),
    );
  }

  Widget _buildPlaylistCard(String title, String subtitle, int songCount, Color color, IconData icon) {
    return Card(
      margin: EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: Container(
          width: 50,
          height: 50,
          decoration: BoxDecoration(
            color: color.withOpacity(0.1),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(icon, color: color, size: 24),
        ),
        title: Text(
          title,
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
        ),
        subtitle: Text(subtitle),
        trailing: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Text(
              '$songCount',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
            ),
            Text('songs', style: TextStyle(fontSize: 12, color: Colors.grey)),
          ],
        ),
        onTap: () {},
      ),
    );
  }

  void _showCreatePlaylistDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Text('Create Playlist'),
        content: TextField(
          decoration: InputDecoration(
            hintText: 'Playlist name',
            border: OutlineInputBorder(),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(context),
            child: Text('Create'),
          ),
        ],
      ),
    );
  }
} 