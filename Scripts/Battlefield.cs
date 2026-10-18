using Godot;
using System;
using System.Collections.Generic;
using System.Linq;

public partial class Battlefield : Node3D
{
    [Export] public int BoardSize { get; set; } = 24;
    private readonly List<TacticalUnit> _units = new();
    private readonly Dictionary<Vector2I, MeshInstance3D> _tiles = new();
    private readonly Dictionary<Vector2I, StandardMaterial3D> _base = new();
    private TacticalUnit? _selected;
    private Camera3D _camera = null!;
    private Label _status = null!;
    private Vector2? _pendingClick;
    private bool _smokeRequested;

    public override void _Ready()
    {
        _camera = GetNode<Camera3D>("Camera3D");
        GetNode<MeshInstance3D>("GroundPreview").Visible = false;
        for (int x=0; x<BoardSize; x++) for (int z=0; z<BoardSize; z++)
        {
            var cell = new Vector2I(x,z);
            var material = new StandardMaterial3D { AlbedoColor = (x+z)%2==0 ? new Color(.34f,.4f,.34f) : new Color(.28f,.34f,.28f), Roughness = .9f };
            var mesh = new MeshInstance3D { Position = CellPosition(cell) - new Vector3(0,.08f,0), Mesh = new BoxMesh { Size = new Vector3(.97f,.15f,.97f) }, MaterialOverride = material };
            var body = new StaticBody3D { CollisionLayer=1, CollisionMask=0 };
            body.SetMeta("cell",cell);
            body.AddChild(new CollisionShape3D { Shape=new BoxShape3D { Size=new Vector3(1,.15f,1) } });
            mesh.AddChild(body); AddChild(mesh); _tiles[cell]=mesh; _base[cell]=material;
        }
        var layer = new CanvasLayer(); AddChild(layer);
        var title = new Label { Text="OATHBREAKERS | Godot + C#", Position=new Vector2(20,15), MouseFilter=Control.MouseFilterEnum.Ignore };
        title.AddThemeFontSizeOverride("font_size",24); layer.AddChild(title);
        _status=new Label { Text="Click a character, then an empty tile. WASD: camera | Wheel: zoom | Right-click: deselect", Position=new Vector2(20,52), MouseFilter=Control.MouseFilterEnum.Ignore };
        layer.AddChild(_status);
        Spawn("Assassin","res://Assets/Characters/Assassin/Assassin.glb",new Vector2I(12,12),new Color(.1f,.75f,.85f));
        Spawn("Ashveil","res://Assets/Characters/Ashveil/Ashveil.glb",new Vector2I(14,12),new Color(.9f,.65f,.2f));
        _smokeRequested = OS.GetCmdlineUserArgs().Contains("--smoke-test");
    }

    private void Spawn(string name,string path,Vector2I cell,Color color)
    {
        var unit=new TacticalUnit { Name=name }; AddChild(unit); unit.Initialize(this,name,path,cell,color); _units.Add(unit);
    }
    public Vector3 CellPosition(Vector2I cell) => new(cell.X-(BoardSize-1)/2f,.08f,cell.Y-(BoardSize-1)/2f);
    public void ClearTile(Vector2I cell) => _tiles[cell].MaterialOverride=_base[cell];
    public void ShowPath(List<Vector2I> path)
    {
        foreach(var cell in _tiles.Keys) ClearTile(cell);
        foreach(var cell in path) _tiles[cell].MaterialOverride=new StandardMaterial3D { AlbedoColor=cell==path[^1] ? Colors.Goldenrod : Colors.DarkCyan };
    }
    private void Select(TacticalUnit? unit)
    {
        _selected=unit; foreach(var candidate in _units) candidate.Select(candidate==unit);
        _status.Text=unit==null ? "Click a character to select him." : $"{unit.DisplayName} selected. Click an empty tile.";
    }
    private bool MoveSelected(Vector2I cell)
    {
        if(_selected==null || _units.Any(u=>u.Moving)) return false;
        bool moved=_selected.MoveTo(cell,_units.Where(u=>u!=_selected).Select(u=>u.Cell).ToHashSet());
        _status.Text=moved ? $"{_selected.DisplayName}: walking to {cell}" : "Choose an empty tile."; return moved;
    }
    public void Arrived(TacticalUnit unit) => _status.Text=$"{unit.DisplayName} arrived at {unit.Cell}.";

    public override void _UnhandledInput(InputEvent input)
    {
        if(input is not InputEventMouseButton mouse || !mouse.Pressed) return;
        if(mouse.ButtonIndex==MouseButton.Left) _pendingClick=mouse.Position;
        if(mouse.ButtonIndex==MouseButton.Right) Select(null);
        if(mouse.ButtonIndex==MouseButton.WheelUp) _camera.Size=Mathf.Max(6,_camera.Size-1.5f);
        if(mouse.ButtonIndex==MouseButton.WheelDown) _camera.Size=Mathf.Min(40,_camera.Size+1.5f);
    }
    public override void _PhysicsProcess(double delta)
    {
        if (_smokeRequested) { _smokeRequested=false; SmokeTest(); return; }
        if(_pendingClick is not Vector2 position) return;
        _pendingClick=null;
        var from=_camera.ProjectRayOrigin(position);
        var query=PhysicsRayQueryParameters3D.Create(from,from+_camera.ProjectRayNormal(position)*200,3);
        var hit=GetWorld3D().DirectSpaceState.IntersectRay(query);
        if(hit.Count==0) return;
        var collider=hit["collider"].AsGodotObject();
        if(collider.HasMeta("unit")) Select(collider.GetMeta("unit").AsGodotObject() as TacticalUnit);
        else if(collider.HasMeta("cell")) MoveSelected(collider.GetMeta("cell").AsVector2I());
    }
    public override void _Process(double delta)
    {
        float x=(Input.IsPhysicalKeyPressed(Key.D)?1:0)-(Input.IsPhysicalKeyPressed(Key.A)?1:0);
        float z=(Input.IsPhysicalKeyPressed(Key.S)?1:0)-(Input.IsPhysicalKeyPressed(Key.W)?1:0);
        _camera.Position+=new Vector3(x,0,z).Normalized()*(float)delta*10;
    }
    public void SmokeTest()
    {
        try
        {
            void Check(bool condition,string message) { if(!condition) throw new Exception(message); }
            Check(GridPathfinder.Find(new(0,0),new(-1,0),24,new())==null,"Off-map destination accepted");
            Check(GridPathfinder.Find(new(0,0),new(2,0),3,new(){new(1,0)})?.Count==4,"Path did not avoid obstacle");
            foreach(var unit in _units)
            {
                Check(unit.HasMovementAnimations,"Imported idle/walk animation clips missing");
                var query=PhysicsRayQueryParameters3D.Create(unit.GlobalPosition+Vector3.Up*3,unit.GlobalPosition-Vector3.Up,2);
                var hit=GetWorld3D().DirectSpaceState.IntersectRay(query);
                Check(hit.Count>0 && hit["collider"].AsGodotObject().GetMeta("unit").AsGodotObject()==unit,"Unit click collider failed");
                Select(unit); var other=_units.First(u=>u!=unit); var original=other.Cell;
                Check(!MoveSelected(other.Cell),"Occupied destination accepted");
                var goal=unit.Cell+new Vector2I(0,2);
                Check(MoveSelected(goal),"Movement rejected"); unit.Advance(5);
                Check(unit.Cell==goal && !unit.Moving,"Unit failed to arrive");
                Check(other.Cell==original,"Unselected unit moved");
            }
            GD.Print("GODOT C# SMOKE TEST PASSED: models, idle/walk clips, click colliders, independent movement, occupancy and pathfinding");
            GetTree().Quit(0);
        }
        catch(Exception error) { GD.PushError(error.ToString()); GetTree().Quit(1); }
    }
}
